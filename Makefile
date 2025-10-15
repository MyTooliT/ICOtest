# -- Variables -----------------------------------------------------------------

SPHINX_DIRECTORY := sphinx
SPHINX_INPUT_DIRECTORY := doc/sphinx

# -- Rules ---------------------------------------------------------------------

.PHONY: run
run: check test

.PHONY: setup
setup:
	uv venv --allow-existing
	uv sync --all-extras

.PHONY: test
test:
	uv run pytest -k 'not firmware'

.PHONY: check
check:
	uv run flake8
	uv run mypy icotest
	uv run pylint .

.PHONY: documentation
documentation:
	uv run sphinx-build -M html $(SPHINX_INPUT_DIRECTORY) \
	    $(SPHINX_DIRECTORY)
