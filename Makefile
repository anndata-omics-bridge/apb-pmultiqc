VENV_BIN := .venv/bin

.DEFAULT_GOAL := help
.PHONY: help sync format format-check lint typecheck deps test build check check-full smoke clean

help:  ## Show developer commands
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

sync:  ## Synchronize the locked development environment
	uv sync --locked --group dev

format:  ## Format and autofix source and tests
	$(VENV_BIN)/ruff format src tests scripts
	$(VENV_BIN)/ruff check --fix src tests scripts

format-check:  ## Check formatting without changing files
	$(VENV_BIN)/ruff format --check src tests scripts

lint:  ## Run Ruff lint checks
	$(VENV_BIN)/ruff check src tests scripts

typecheck:  ## Run standard Pyright in strict mode
	$(VENV_BIN)/pyright

deps:  ## Validate dependency declarations
	$(VENV_BIN)/deptry .

test:  ## Run tests with branch coverage
	$(VENV_BIN)/pytest --cov --cov-branch

build:  ## Build and validate source and wheel distributions
	uv build
	$(VENV_BIN)/twine check dist/*

check:  ## Run every merge-blocking quality gate
	uv lock --check
	$(MAKE) format-check lint typecheck deps test build

smoke: build  ## Install the locked environment and wheel outside the checkout; generate a report
	$(VENV_BIN)/python -m scripts.smoke

check-full: check  ## Run quality gates and clean-install acceptance
	$(VENV_BIN)/python -m scripts.smoke

clean:  ## Remove generated build and quality artifacts
	$(VENV_BIN)/python -c "import shutil; [shutil.rmtree(path, ignore_errors=True) for path in ('build', 'dist', '.pytest_cache', '.ruff_cache')]"
