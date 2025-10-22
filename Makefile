# -- Variables -----------------------------------------------------------------

SPHINX_DIRECTORY := sphinx
SPHINX_INPUT_DIRECTORY := doc/sphinx

TEST_COMMAND := uv run pytest -k 'not firmware_upload'

# -- Rules ---------------------------------------------------------------------

.PHONY: run
run: check test

.PHONY: setup
setup:
	uv venv --allow-existing
	uv sync --all-extras

.PHONY: test
test:
	$(TEST_COMMAND) || ( uv run icon stu reset && \
	                     $(TEST_COMMAND) --last-failed )

.PHONY: check
check:
	uv run flake8
	uv run mypy icotest
	uv run pylint .

.PHONY: documentation
documentation:
	uv run sphinx-build -M html $(SPHINX_INPUT_DIRECTORY) \
	    $(SPHINX_DIRECTORY)
