# Locked dependencies

The application uses immutable, remotely available APB commits selected at implementation start. Local-only commits and working-tree changes are excluded.

| Distribution | Commit |
| --- | --- |
| apb-export | [`33ae6a855df7`](https://github.com/anndata-omics-bridge/apb-export/commit/33ae6a855df79197ed4efc0b6ba1d6ebbbc9bc33) |
| apb2 | [`9c6b088b4500`](https://github.com/anndata-omics-bridge/apb2/commit/9c6b088b45000407a2b4066cd8b90e3c1d686059) |
| apb-catalog | [`abf736678027`](https://github.com/anndata-omics-bridge/apb-catalog/commit/abf7366780275ff953414b0841b9fa890cc62940) |
| apb-fasta | [`5830b080542e`](https://github.com/anndata-omics-bridge/apb-fasta/commit/5830b080542ed59ec4e40d7ca65e590c5beafe2e) |
| protein-fasta | [`4048b16bcce8`](https://github.com/anndata-omics-bridge/protein-fasta/commit/4048b16bcce895ca5d7a774d2ec0c11bb9bd34e2) |
| prozor | [`ab7c41bdfbbe`](https://github.com/anndata-omics-bridge/prozor/commit/ab7c41bdfbbe877d66236c5c33549b7747426ace) |

pMultiQC is pinned to the tested [integration commit `ae84c631650f`](https://github.com/wolski/pmultiqc/commit/ae84c631650faa91c40dd0212289c26002c0c4b7). It contains [upstream RT PR #751](https://github.com/bigbio/pmultiqc/pull/751) plus pyOpenMS 3.5 support: the newer native peptide container in both idXML paths, and a compatible dependency range. This keeps the QPX reader unchanged apart from the submitted null-RT fix. MultiQC remains 1.35; pyOpenMS is explicitly locked to 3.5.0, which provides a Linux ARM wheel.

The RT PR remains open. The separate ARM compatibility patch has not been submitted upstream because its PR workflow would automatically run large example datasets, outside the user's current small-file limit. The patch passed the existing upstream unit suite (258 passed, two existing skips), four focused idXML checks, and a new tiny synthetic consensus round trip. No installed package is patched. Adopt merged upstream revisions through a deliberate dependency update.

Change selected Git references or package constraints, regenerate `uv.lock`, then run `make check-full`. Use `uv sync --locked` for ordinary installation; stale manifests must fail rather than update dependencies implicitly. Runtime provenance records installed versions and Git sources in each report’s `run.json`.
