"""Small synthetic vendor input shared by the application tests and wheel smoke check."""

from __future__ import annotations

from pathlib import Path

from apb2.api import ParsedLevels, ParseRuleCompiler, write_parsed_levels

RUNS = ("run_A1", "run_A2", "run_B1", "run_B2")
SEQUENCES = ("PEPTIDEK", "SECONDK", "THIRDPEPK", "FOURTHPEPK", "FIFTHPEPK", "LASTPEPK")


def parsed_result(folder: Path, with_rt: bool = True) -> ParsedLevels:
    """Parse known DIA-NN values, including a protein group with two members."""
    columns = [
        "Run",
        "Modified.Sequence",
        "Stripped.Sequence",
        "Precursor.Charge",
        "Precursor.Id",
        "Protein.Group",
        "Protein.Ids",
        "Protein.Names",
        "Genes",
        "Precursor.Quantity",
        "Precursor.Normalised",
        "Q.Value",
        "Global.Q.Value",
        "Lib.Q.Value",
        "PEP",
        "PG.MaxLFQ",
        "PG.Q.Value",
        "Lib.PG.Q.Value",
        "Global.PG.Q.Value",
    ]
    if with_rt:
        columns.append("RT")
    rows = ["\t".join(columns)]
    for run_index, run in enumerate(RUNS):
        for index, sequence in enumerate(SEQUENCES):
            if (run_index + index) % 5 == 4:
                continue
            group = "P3;P7" if index == 2 else f"P{index + 1}"
            scale = (index + 1) * (run_index + 1)
            values: list[str | int | float] = [
                run,
                sequence,
                sequence,
                2,
                sequence + "2",
                group,
                group,
                group,
                f"G{index}",
                1000 * scale,
                900 * scale,
                0.001,
                0.002,
                0,
                0.01,
                500 * scale,
                0.001,
                0,
                0.002,
            ]
            if with_rt:
                values.append(10.0 + index + run_index)
            rows.append("\t".join(map(str, values)))
    report = folder / "report.tsv"
    report.write_text("\n".join(rows) + "\n", encoding="utf-8")
    params = folder / "report.log.txt"
    params.write_text("DIA-NN 1.8.1 (Data-Independent Acquisition by Neural Networks)\n")
    return (
        ParseRuleCompiler.detect(report, params, requested_levels=("peptidoform_ion", "protein"))
        .compile()
        .parse()
    )


def stored_result(folder: Path, suffix: str = ".parquet") -> Path:
    """Write a canonical APB result with the public APB2 writer."""
    target = folder / f"input{suffix}"
    write_parsed_levels(parsed_result(folder), target)
    return target
