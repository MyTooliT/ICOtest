# ICOtest

## Install

### Poetry

We recommend you use [Poetry](https://python-poetry.org) to install the package. To do that please use the following commands in the root of the repository:

```sh
poetry lock
poetry install --all-extras
```

### Pip

To install the package

- in development/editable mode
- including development (`dev`) packages

please use the following command in the root of the repository:

```
pip install -e .[dev]
```

#### Uninstall

```sh
pip uninstall icotest
```

## Tests

To run the test, please use the following command in the root of the repository:

```sh
poetry run pytest
```
