"""Actual pMultiQC reports and explicit failure contracts of the CLI."""

from __future__ import annotations

import json
import subprocess
from dataclasses import replace
from pathlib import Path
from typing import TextIO

import polars as pl
import pytest
from apb2.api import AnnotationCompiler, ParsedLevels, write_parsed_levels
from scripts.synthetic import RUNS, parsed_result

from apb_pmultiqc.cli import app, main


def _run(source: Path, output: Path, *args: str) -> int:
    return app([str(source), str(output), *args], result_action="return_value")


def _record(output: Path) -> dict[str, object]:
    return json.loads((output / "run.json").read_text())


@pytest.mark.parametrize("suffix", [".h5mu", ".duckdb", ".parquet"])
@pytest.mark.parametrize(
    "levels", [("peptidoform_ion",), ("protein",), ("peptidoform_ion", "protein")]
)
def test_reports_all_formats_and_available_levels(
    parsed: ParsedLevels, tmp_path: Path, suffix: str, levels: tuple[str, ...]
) -> None:
    source = tmp_path / f"input{suffix}"
    selected = replace(parsed, levels={name: parsed.levels[name] for name in levels})
    write_parsed_levels(selected, source)
    output = tmp_path / "report"

    assert _run(source, output) == 0

    record = _record(output)
    assert record["state"] == "complete" and record["multiqc_exit_code"] == 0
    assert (output / "multiqc_report.html").stat().st_size > 100_000
    plots = json.loads((output / "multiqc_data/multiqc_data.json").read_text())["report_plot_data"]
    assert "identification_summary_table" in plots
    if "peptidoform_ion" in levels:
        features = pl.read_parquet(output / "data.qpx/apb.feature.parquet")
        assert features.height == 20
        assert features.get_column("rt").min() == 600.0
        assert "peptide_intensity_distribution_box" in plots
    if "protein" in levels:
        proteins = pl.read_parquet(output / "data.qpx/apb.pg.parquet")
        assert proteins.height == 20
        assert proteins.filter(pl.col("pg_accessions").list.len() == 2).height > 0
        assert "protein_intensity_distribution_box" in plots
    assert "Failed to generate" not in (output / "execution.log").read_text()


@pytest.mark.parametrize("level", ["protein", "peptidoform_ion"])
def test_standalone_h5ad(parsed: ParsedLevels, tmp_path: Path, level: str) -> None:
    source = tmp_path / "input.h5ad"
    write_parsed_levels(replace(parsed, levels={level: parsed.levels[level]}), source)
    output = tmp_path / "report"
    assert _run(source, output) == 0
    assert _record(output)["state"] == "complete"


def test_no_rt_needs_no_application_workaround(tmp_path: Path) -> None:
    parsed = parsed_result(tmp_path, with_rt=False)
    source = tmp_path / "input.parquet"
    write_parsed_levels(parsed, source)
    output = tmp_path / "report"
    assert _run(source, output) == 0
    assert _record(output)["state"] == "complete"
    assert "Failed to generate plot_rt" not in (output / "execution.log").read_text()


def test_optional_group_annotation_is_carried_to_the_report(
    parsed: ParsedLevels, tmp_path: Path
) -> None:
    annotation = tmp_path / "samples.tsv"
    annotation.write_text("raw_file\tcondition\n" + "".join(f"{run}\t{run[4]}\n" for run in RUNS))
    annotated = AnnotationCompiler().compile(annotation).parse(parsed).annotate().parsed
    source = tmp_path / "input.parquet"
    write_parsed_levels(annotated, source)
    output = tmp_path / "report"
    assert _run(source, output) == 0
    samples = pl.read_parquet(output / "data.qpx/apb.sample.parquet")
    assert dict(samples.select("sample_accession", "condition").iter_rows()) == {
        "run_A1": "A",
        "run_A2": "A",
        "run_B1": "B",
        "run_B2": "B",
    }
    plots = json.loads((output / "multiqc_data/multiqc_data.json").read_text())["report_plot_data"]
    assert "experimental_design" in plots


def test_refuses_existing_output_without_changing_it(source: Path, tmp_path: Path) -> None:
    output = tmp_path / "report"
    output.mkdir()
    (output / "keep").write_text("preserve")
    assert _run(source, output) == 1
    assert list(output.iterdir()) == [output / "keep"]
    assert (output / "keep").read_text() == "preserve"


def test_missing_input_and_bad_timeout_create_no_output(source: Path, tmp_path: Path) -> None:
    output = tmp_path / "report"
    assert _run(tmp_path / "missing.parquet", output) == 1
    assert _run(source, output, "--timeout", "0") == 1
    assert not output.exists()


def test_directory_input_stays_read_only(source: Path) -> None:
    before = sorted(source.rglob("*"))
    assert _run(source, source / "report") == 1
    assert sorted(source.rglob("*")) == before


@pytest.mark.parametrize(
    "contents",
    [
        None,
        "[]",
        "{}",
        '{"report_plot_data": {}}',
        '{"report_plot_data": {"identification_summary_table": {}}}',
        '{"report_plot_data": {"identification_summary_table": {"datasets": []}}}',
    ],
)
def test_zero_exit_without_a_real_report_is_failure(
    source: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, contents: str | None
) -> None:
    def incomplete(
        args: list[str],
        cwd: Path,
        stdout: TextIO,
        stderr: int,
        text: bool,
        timeout: int,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        del stdout, stderr, text, timeout, check
        if contents is not None:
            (cwd / "multiqc_report.html").write_text("<html>partial</html>")
            (cwd / "multiqc_data").mkdir()
            (cwd / "multiqc_data/multiqc_data.json").write_text(contents)
        return subprocess.CompletedProcess(args, returncode=0)

    monkeypatch.setattr("subprocess.run", incomplete)
    output = tmp_path / "report"
    assert _run(source, output) == 1
    record = _record(output)
    assert record["state"] == "failed" and record["multiqc_exit_code"] == 0


def test_bad_apb_input_retains_diagnostics(tmp_path: Path) -> None:
    source = tmp_path / "bad.h5ad"
    source.write_text("not an APB result")
    output = tmp_path / "report"
    assert _run(source, output) == 1
    assert _record(output)["state"] == "failed"
    assert "Report generation failed" in (output / "execution.log").read_text()


def _completed(
    args: list[str], cwd: Path, stdout: TextIO, stderr: int, text: bool, timeout: int, check: bool
) -> subprocess.CompletedProcess[str]:
    del cwd, stdout, stderr, text, timeout, check
    return subprocess.CompletedProcess(args, returncode=17)


def test_nonzero_exit_is_failure_with_qpx_retained(
    source: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("subprocess.run", _completed)
    output = tmp_path / "report"
    assert _run(source, output) == 1
    record = _record(output)
    assert record["state"] == "failed" and record["multiqc_exit_code"] == 17
    assert (output / "data.qpx/export.json").is_file()


@pytest.mark.parametrize(
    "message",
    [
        "2026-01-01 [ERROR] reader: failed plot\n",
        " qpx | Failed to generate plot_rt\n",
        "Traceback (most recent call last):\n",
    ],
)
def test_zero_exit_does_not_hide_logged_plot_errors(
    source: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, message: str
) -> None:
    def failing_plot(
        args: list[str],
        cwd: Path,
        stdout: TextIO,
        stderr: int,
        text: bool,
        timeout: int,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        del cwd, stderr, text, timeout, check
        stdout.write(message)
        return subprocess.CompletedProcess(args, returncode=0)

    monkeypatch.setattr("subprocess.run", failing_plot)
    output = tmp_path / "report"
    assert _run(source, output) == 1
    record = _record(output)
    assert record["state"] == "failed" and record["multiqc_exit_code"] == 0
    assert "plot error" in str(record["error"])


def test_timeout_is_failure(source: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def timed_out(
        args: list[str],
        cwd: Path,
        stdout: TextIO,
        stderr: int,
        text: bool,
        timeout: int,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        del cwd, stdout, stderr, text, check
        raise subprocess.TimeoutExpired(args, timeout)

    monkeypatch.setattr("subprocess.run", timed_out)
    output = tmp_path / "report"
    assert _run(source, output, "--timeout", "1") == 1
    assert "TimeoutExpired" in str(_record(output)["error"])


def test_main_propagates_status(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "sys.argv", ["apb-pmultiqc", str(tmp_path / "missing.parquet"), str(tmp_path / "out")]
    )
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 1
