"""Stored APB results to QPX and an unchanged pMultiQC report."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path
from typing import Annotated, cast

from apb2.api import JsonValue, read_parsed_levels
from apb_export.api import Exporter
from cyclopts import App, Parameter
from loguru import logger

app = App(name="apb-pmultiqc", help="Generate a pMultiQC report from a stored APB result.")
_PACKAGES = (
    "apb-pmultiqc",
    "apb-export",
    "apb2",
    "apb-catalog",
    "apb-fasta",
    "protein-fasta",
    "prozor",
    "pmultiqc",
    "multiqc",
    "pyopenms",
)
_PLOT_ERROR = re.compile(
    r"(?m)^.*\[(?:ERROR|CRITICAL)\].*$|"
    r"^.*\|\s*(?:ERROR|CRITICAL)\b.*$|"
    r"^.*\|\s*Failed to generate\b.*$|^Traceback \(most recent call last\):"
)


def _object(text: str) -> dict[str, JsonValue]:
    """Read a JSON object at an external data boundary."""
    value: object = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError("expected a JSON object")
    return cast(dict[str, JsonValue], value)


def _environment() -> dict[str, JsonValue]:
    """Record installed package versions and their immutable Git source metadata."""
    packages: dict[str, JsonValue] = {}
    for name in _PACKAGES:
        distribution = metadata.distribution(name)
        entry: dict[str, JsonValue] = {"version": distribution.version}
        direct = distribution.read_text("direct_url.json")
        if direct is not None:
            entry["source"] = _object(direct)
        packages[name] = entry
    return packages


def _save(output: Path, record: dict[str, JsonValue]) -> None:
    """Persist the run's state and provenance beside its report and diagnostics."""
    (output / "run.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


def _plots(output: Path) -> int:
    """Require a nonempty HTML report and the QPX summary plot in its report data."""
    page = output / "multiqc_report.html"
    if not page.is_file() or page.stat().st_size == 0:
        raise ValueError("MultiQC produced no HTML report")
    data = _object((output / "multiqc_data/multiqc_data.json").read_text(encoding="utf-8"))
    plots = data.get("report_plot_data")
    if not isinstance(plots, dict) or "identification_summary_table" not in plots:
        raise ValueError("MultiQC produced no populated QPX summary plot")
    summary = plots["identification_summary_table"]
    if not isinstance(summary, dict) or not summary.get("datasets"):
        raise ValueError("MultiQC produced an empty QPX summary plot")
    return len(plots)


def _generate(source: Path, output: Path, timeout: int, record: dict[str, JsonValue]) -> None:
    """Read through APB2, serialize through APB Export and invoke the installed reader."""
    logger.info("Reading APB result: {}", source)
    parsed = read_parsed_levels(source)
    exporter = Exporter("qpx")
    qpx = output / "data.qpx"
    exporter.write(exporter.export(parsed), qpx)
    command = [sys.executable, "-m", "multiqc", "--qpx-plugin", str(qpx), "--outdir", str(output)]
    record["command"] = list[JsonValue](command)
    _save(output, record)
    logger.info("Generating pMultiQC report; timeout={} seconds", timeout)
    log_path = output / "execution.log"
    with log_path.open("a", encoding="utf-8") as log:
        result = subprocess.run(
            command,
            cwd=output,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
            check=False,
        )
    record["multiqc_exit_code"] = result.returncode
    if result.returncode != 0:
        raise RuntimeError(f"MultiQC exited with status {result.returncode}; see {log_path}")
    if _PLOT_ERROR.search(log_path.read_text(encoding="utf-8")):
        raise RuntimeError(f"MultiQC logged a report or plot error; see {log_path}")
    record["plots"] = _plots(output)


@app.default
def report(
    source: Annotated[Path, Parameter(help="Stored APB HDF5, DuckDB or Parquet result")],
    output: Annotated[Path, Parameter(help="New directory for QPX tables, report and diagnostics")],
    /,
    *,
    timeout: Annotated[int, Parameter(help="Maximum MultiQC runtime in seconds")] = 1800,
) -> int:
    """Generate a report from existing APB quantities; grouping and RT are optional."""
    source, output = source.resolve(), output.absolute()
    if timeout <= 0:
        logger.error("timeout must be positive")
        return 1
    if not source.exists():
        logger.error("APB input does not exist: {}", source)
        return 1
    if source.is_dir() and output.resolve().is_relative_to(source):
        logger.error("Output must be outside the input result directory: {}", source)
        return 1
    try:
        output.mkdir(parents=True, exist_ok=False)
    except OSError as error:
        logger.error("Cannot create new output directory {}: {}", output, error)
        return 1
    started = time.monotonic()
    record: dict[str, JsonValue] = {
        "schema_version": "1",
        "state": "running",
        "input": str(source),
        "started_at": datetime.now(UTC).isoformat(),
        "timeout_seconds": timeout,
    }
    handler = logger.add(output / "execution.log", encoding="utf-8")
    try:
        record["environment"] = _environment()
        _save(output, record)
        _generate(source, output, timeout, record)
        record["state"] = "complete"
        logger.success("Report: {}", output / "multiqc_report.html")
        return 0
    except Exception as error:
        # This CLI boundary retains the full traceback and exits nonzero. A reader that
        # logs a swallowed plot exception is also a failed run, never a partial success.
        record["state"] = "failed"
        record["error"] = {"type": type(error).__name__, "message": str(error)}
        logger.exception("Report generation failed: {}", error)
        return 1
    finally:
        if record["state"] == "running":
            record["state"] = "failed"
            record["error"] = {"type": "Interrupted", "message": "Report generation interrupted"}
        record["finished_at"] = datetime.now(UTC).isoformat()
        record["elapsed_seconds"] = time.monotonic() - started
        try:
            _save(output, record)
        finally:
            logger.remove(handler)


def main() -> None:
    """Exit with the application command's status."""
    raise SystemExit(app(result_action="return_value"))


if __name__ == "__main__":
    main()
