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
