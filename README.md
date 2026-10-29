# APB pMultiQC

Generate a pMultiQC report from a stored APB result. APB2 reads the result, APB Export writes QPX Parquet tables, and the installed pMultiQC QPX reader generates the report.

```bash
git clone https://github.com/anndata-omics-bridge/apb-pmultiqc.git
cd apb-pmultiqc
uv sync --locked --no-dev
uv run --locked --no-dev apb-pmultiqc result.h5mu report
```

Python 3.13 or later, Git and uv 0.12.17 are required. Use the committed application lock: it pins the tested APB stack, pMultiQC and all transitive dependencies independently of local APB development.

## Inputs and outputs

- Stored APB `.h5ad`, `.h5mu`, `.duckdb` or `.parquet` results, including their APB metadata sidecars
- Existing precursor quantities, protein quantities, or both; no aggregation or vendor re-parsing
- Grouping, organism, FASTA, SDRF and retention times optional; supplied sample annotations carried into QPX
- RT resolved by APB Export through the chromatography catalogue and converted to seconds; unresolved original units fail explicitly
- New output directory required, outside a directory input; existing outputs never overwritten

The output contains `data.qpx/` (Parquet tables and exporter provenance), `multiqc_report.html`, `multiqc_data/`, `execution.log` and `run.json`. The run record contains state, input, timestamps, installed versions and Git revisions, the exact command and failure details. The HTML report is self-contained; keep the other files for reproducibility and diagnostics.

```bash
uv run --locked --no-dev apb-pmultiqc result.parquet report --timeout 600
```

The timeout bounds the MultiQC subprocess, in seconds (default 1800). Conversion errors, process failures, timeouts, logged report/plot errors and reports without a populated QPX summary return a nonzero status and retain diagnostics. Normal upstream warnings remain in the log. Organism-based feature-grouping plots are not currently exposed by pMultiQC's QPX reader.

## Dependency provenance

The lock uses a tested source commit containing [pMultiQC PR #751](https://github.com/bigbio/pmultiqc/pull/751), fixing absent/all-null RT plots. That PR was merged on 29 October 2026; no pMultiQC release contains it yet (the latest is 0.0.48), so the source pin stays until one does. The source pin also includes pyOpenMS 3.5 container compatibility for Linux ARM; no installed reader is patched. The pinned APB revisions and deliberate upgrade process are in [dependency provenance](docs/dependencies.md).

## Development

```bash
uv sync --locked --group dev
make check
make check-full
.venv/bin/pre-commit install --hook-type pre-commit --hook-type pre-push
```

`make check` covers lock consistency, Ruff, strict Pyright, dependency declarations, synthetic end-to-end reports and distribution validation. `make check-full` also installs the locked runtime dependencies and built wheel into a fresh environment outside the checkout, verifies all seven Git pins and generates a report there. CI runs the full gate from this repository alone. No external vendor fixtures or corpus runs are needed.

Generated from the workspace Python package Copier template. MIT license; application version 0.1.1. Report generation belongs here; QPX serialization remains in [APB Export](https://github.com/anndata-omics-bridge/apb-export), and the separately locked [web UI](https://github.com/anndata-omics-bridge/apb-export-ui) pins this application and runs `apb-pmultiqc` for its QPX reports.
