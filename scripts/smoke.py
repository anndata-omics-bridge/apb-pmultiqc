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


def installed_check() -> str:
    """Build assertions runnable with only the installed environment and standard library."""
    dependencies = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["dependencies"]
    expected = {
        entry.split(" @ ")[0]: entry.rsplit("@", 1)[1]
        for entry in dependencies
        if " @ git+" in entry
    }
    return f"""
import importlib.metadata as metadata
import json
import apb_pmultiqc
expected = {expected!r}
assert len(expected) == 7
for name, revision in expected.items():
    distribution = metadata.distribution(name)
    direct = json.loads(distribution.read_text("direct_url.json"))
    assert not direct.get("dir_info", {{}}).get("editable", False), (name, direct)
    assert direct["vcs_info"]["commit_id"] == revision, (name, direct)
owners = [d.metadata["Name"] for d in metadata.distributions() if any(
    e.name == "apb-pmultiqc" and e.group == "console_scripts" for e in d.entry_points)]
assert owners == ["apb-pmultiqc"], owners
assert {str(ROOT)!r} not in apb_pmultiqc.__file__, apb_pmultiqc.__file__
print("Isolated wheel owns its executable and matches all seven immutable Git pins")
"""


def main() -> None:
    """Install exact locked dependencies, verify provenance and generate a real report."""
    wheel = next((ROOT / "dist").glob("*.whl"))
    with tarfile.open(next((ROOT / "dist").glob("*.tar.gz"))) as archive:
        names = archive.getnames()
        assert not any("__pycache__" in name or "/.venv/" in name for name in names)
        for required in ("uv.lock", ".python-version", "docs/dependencies.md", "scripts/smoke.py"):
            assert any(name.endswith("/" + required) for name in names), required
    with tempfile.TemporaryDirectory(prefix="apb-pmultiqc-wheel-") as directory:
        folder = Path(directory)
        environment = folder / "venv"
        subprocess.run(["uv", "venv", "--python", "3.13", str(environment)], check=True)
        requirements = folder / "requirements.txt"
        requirements.write_bytes(
            subprocess.check_output(
                ["uv", "export", "--locked", "--no-dev", "--no-emit-project", "--no-hashes"],
                cwd=ROOT,
            )
        )
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
