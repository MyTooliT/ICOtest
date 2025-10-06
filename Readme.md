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
pytest # or `poetry run pytest`
```

### Configuration

1. Open the configuration file in your default text editor:

   ```sh
   icotest config # or `poetry run icotest config`
   ```

2. Adapt the configuration

### Debug

To enable the output of log messages in the code, please add the following config settings:

```toml
log_cli = true
log_cli_level = "INFO"
```

to the table `tool.pytest.ini_options` in `pyproject.toml`.
