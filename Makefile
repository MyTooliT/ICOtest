# -- Variables -----------------------------------------------------------------

SPHINX_DIRECTORY := sphinx
SPHINX_INPUT_DIRECTORY := doc/sphinx

# -- Rules ---------------------------------------------------------------------

.PHONY: run
run: check test

.PHONY: test
test:
	poetry run pytest

.PHONY: check
check:
	poetry run flake8
	poetry run mypy icotest
	poetry run pylint .

.PHONY: documentation
documentation:
	poetry run sphinx-build -M html $(SPHINX_INPUT_DIRECTORY) \
	    $(SPHINX_DIRECTORY)
