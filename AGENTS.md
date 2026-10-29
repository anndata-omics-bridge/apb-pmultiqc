# APB pMultiQC — agent rules

Python 3.13+ report application generated from the workspace Copier template. Explicit user instructions override this file; preserve unrelated changes.

## Commands

Run from the repository root; Python tools use its synchronized virtual environment.

| Task | Command |
| --- | --- |
| Synchronize | `uv sync --locked --group dev` |
| Format | `make format` |
| Lint | `make lint` |
| Typecheck | `make typecheck` |
| Dependencies | `make deps` |
| Tests | `make test` |
| Build | `make build` |
| Before commit | `make check` |
| Before push | `make check-full` |

## Architecture

- [CLI](src/apb_pmultiqc/cli.py): APB2 public stored-result reader → APB Export public QPX target → installed MultiQC subprocess
- No public Python library API; `__init__.py` stays empty. Another workspace package is imported only through its `api.py`, enforced by [import checks](tests/test_sibling_imports.py)
- Conversion and catalogue semantics belong upstream. Never hardcode vendor field names or patch installed pMultiQC; errors remain visible
- Preserve QPX tables, report data, provenance and logs; refuse overwrite and return nonzero on partial reports, logged plot errors or timeouts
- [Synthetic input](scripts/synthetic.py) and [clean-install smoke](scripts/smoke.py) need no external data or sibling test packages

## Quality and dependencies

- Fully annotate functions, including tests, scripts, callbacks and fixtures. Ruff and strict Pyright are mandatory; no blanket exclusions, baselines or unqualified ignores
- Declare direct runtime imports and invoked applications; put test/build tools in the development group. Use standard library and existing dependencies before adding another
- This is an application: **commit [uv.lock](uv.lock)**. All APB Git dependencies and the upstream reader fix, merged but not yet released, use full immutable SHAs; no sibling path/editable sources or moving branches
- Use uv 0.12.17 and `--locked` for ordinary installs. Upgrade selected pins, regenerate the lock, run the full gate and update [dependency provenance](docs/dependencies.md)
- CI checks a standalone checkout. The full gate installs the wheel outside this checkout and verifies installed source revisions; do not replace that check with a development-path install
- Test synthetic reports for every supported APB format and available level. Do not weaken scientific assertions to accommodate an extraction or dependency error

Planning belongs in the workspace TODO repository under this application's owner. No production deployment, publication to PyPI or corpus run is implied by this repository's gates.
