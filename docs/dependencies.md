# Locked dependencies

APB packages are PyPI ranges, from the paper releases on; `uv.lock` pins the tested versions: apb-export 0.2.2, apb2 0.1.4 with its DuckDB extra, apb-catalog 0.1.6, apb-fasta 0.1.2, protein-fasta 0.3.2 and prozor 0.1.2. The DuckDB extra lets the application read `.duckdb` results.

pMultiQC is pinned to the tested [integration commit `ae84c631650f`](https://github.com/wolski/pmultiqc/commit/ae84c631650faa91c40dd0212289c26002c0c4b7). It contains [upstream RT PR #751](https://github.com/bigbio/pmultiqc/pull/751) plus pyOpenMS 3.5 support: the newer native peptide container in both idXML paths, and a compatible dependency range. This keeps the QPX reader unchanged apart from the submitted null-RT fix. MultiQC remains 1.35; pyOpenMS is explicitly locked to 3.5.0, which provides a Linux ARM wheel.

The RT PR was merged on 29 October 2026; no pMultiQC release contains it yet (the latest is 0.0.48), so the integration commit stays pinned until one does. The separate ARM compatibility patch has not been submitted upstream because its PR workflow would automatically run large example datasets, outside the user's current small-file limit. The patch passed the existing upstream unit suite (258 passed, two existing skips), four focused idXML checks, and a new tiny synthetic consensus round trip. No installed package is patched. Adopt merged upstream revisions through a deliberate dependency update.

Change selected package constraints or the pMultiQC reference, regenerate `uv.lock`, then run `make check-full`. Use `uv sync --locked` for ordinary installation; stale manifests must fail rather than update dependencies implicitly. Runtime provenance records installed versions and Git sources in each report’s `run.json`.
