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

pMultiQC is pinned to [`8829884d69d2`](https://github.com/bigbio/pmultiqc/commit/8829884d69d28d0d0a75086dec0bf7f45e381b4d), the tested head of [upstream PR #751](https://github.com/bigbio/pmultiqc/pull/751). The PR is not merged at this application’s initial implementation. It fixes plots for absent/all-null retention times; the application applies no runtime patch. MultiQC is pinned to 1.35.

Change selected Git references or package constraints, regenerate `uv.lock`, then run `make check-full`. Use `uv sync --locked` for ordinary installation; stale manifests must fail rather than update dependencies implicitly. Runtime provenance records installed versions and Git sources in each report’s `run.json`.
