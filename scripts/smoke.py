"""Verify a clean locked wheel installation and report outside the source checkout."""

from __future__ import annotations

import json
import subprocess
import tarfile
import tempfile
import tomllib
from pathlib import Path

from scripts.synthetic import stored_result

ROOT = Path(__file__).resolve().parents[1]


APB_PACKAGES = frozenset(
    {"apb-export", "apb2", "apb-catalog", "apb-fasta", "protein-fasta", "prozor", "pmultiqc"}
)


def locked_requirements() -> bytes:
    """The application's locked runtime requirements."""
    return subprocess.check_output(
        ["uv", "export", "--locked", "--no-dev", "--no-emit-project", "--no-hashes"], cwd=ROOT
    )


def installed_check() -> str:
    """Build assertions runnable with only the installed environment and standard library: the
    APB packages and pMultiQC installed as the lock pins them, by version or Git commit."""
    expected: dict[str, tuple[str, str]] = {}
    for line in locked_requirements().decode().splitlines():
        entry = line.split(";", 1)[0].strip()
        if " @ git+" in entry:
            name, url = entry.split(" @ ", 1)
            expected[name] = ("commit", url.rsplit("@", 1)[1])
        elif "==" in entry:
            name, version = entry.split("==", 1)
            expected[name] = ("version", version)
    expected = {name: pin for name, pin in expected.items() if name in APB_PACKAGES}
    assert expected.keys() == APB_PACKAGES, expected
    return f"""
import importlib.metadata as metadata
import json
import apb_pmultiqc
expected = {expected!r}
for name, (kind, pin) in expected.items():
    distribution = metadata.distribution(name)
    origin = distribution.read_text("direct_url.json")
    direct = json.loads(origin) if origin else {{}}
    assert not direct.get("dir_info", {{}}).get("editable", False), (name, direct)
    if kind == "commit":
        assert direct["vcs_info"]["commit_id"] == pin, (name, direct)
    else:
        assert distribution.version == pin, (name, distribution.version)
owners = [d.metadata["Name"] for d in metadata.distributions() if any(
    e.name == "apb-pmultiqc" and e.group == "console_scripts" for e in d.entry_points)]
assert owners == ["apb-pmultiqc"], owners
assert {str(ROOT)!r} not in apb_pmultiqc.__file__, apb_pmultiqc.__file__
print("Isolated wheel owns its executable and matches every locked APB and pMultiQC pin")
"""


def main() -> None:
    """Install exact locked dependencies, verify provenance and generate a real report."""
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    stem = f"{project['name'].replace('-', '_')}-{project['version']}"
    wheel = ROOT / "dist" / f"{stem}-py3-none-any.whl"
    with tarfile.open(ROOT / "dist" / f"{stem}.tar.gz") as archive:
        names = archive.getnames()
        assert not any("__pycache__" in name or "/.venv/" in name for name in names)
        for required in ("uv.lock", ".python-version", "docs/dependencies.md", "scripts/smoke.py"):
            assert any(name.endswith("/" + required) for name in names), required
    with tempfile.TemporaryDirectory(prefix="apb-pmultiqc-wheel-") as directory:
        folder = Path(directory)
        environment = folder / "venv"
        subprocess.run(["uv", "venv", "--python", "3.13", str(environment)], check=True)
        requirements = folder / "requirements.txt"
        requirements.write_bytes(locked_requirements())
        python = environment / "bin/python"
        subprocess.run(
            [
                "uv",
                "pip",
                "install",
                "--python",
                str(python),
                "--no-deps",
                "-r",
                str(requirements),
                str(wheel),
            ],
            check=True,
        )
        subprocess.run([str(python), "-c", installed_check()], cwd=folder, check=True)
        source = stored_result(folder)
        output = folder / "report"
        subprocess.run(
            [
                str(environment / "bin/apb-pmultiqc"),
                str(source),
                str(output),
                "--timeout",
                "120",
            ],
            cwd=folder,
            check=True,
        )
        record = json.loads((output / "run.json").read_text())
        assert record["state"] == "complete", record
        assert record["multiqc_exit_code"] == 0
        assert record["plots"] >= 10
        assert (output / "data.qpx/apb.feature.parquet").is_file()
        assert (output / "data.qpx/apb.pg.parquet").is_file()
        assert (output / "multiqc_report.html").stat().st_size > 100_000
        print(f"Clean installed report passed: {record['plots']} populated plots")


if __name__ == "__main__":
    main()
