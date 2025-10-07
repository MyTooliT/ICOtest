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
[tool.pytest.ini_options]
# Add the values below:
log_cli = true
log_cli_level = "INFO"
```

to `pyproject.toml`. The value besides `log_cli_level` is the minimum level of log messages, that will be displayed by the test code. For the value `INFO`, all log messages with level `INFO` or higher (e.g. `logger.info`, `logger.warning`, `logger.error`) will be included in the output.

## Development

### Release

**Note:** In the text below we assume that you want to release version `<VERSION>` of the package. Please just replace this version number with the version that you want to release (e.g. `0.2`).

1. Make sure that all the checks and tests work correctly locally

   ```sh
   make
   ```

2. Make sure all [workflows of the CI system work correctly](https://github.com/MyTooliT/ICOtest/actions)

3. Release a new version on [PyPI](https://pypi.org/project/icotest/):
   1. Increase version number
   2. Add git tag containing version number
   3. Push changes

   ```sh
   poetry version <VERSION>
   export icotest_version="$(poetry version -s)"
   git commit -a -m "Release: Release version $icotest_version"
   git tag "$icotest_version"
   git push && git push --tags
   ```

4. Open the [release notes](https://github.com/MyTooliT/ICOtest/tree/main/doc/release) for the latest version and [create a new release](https://github.com/MyTooliT/ICOtest/releases/new)
   1. Paste them into the main text of the release web page
   2. Insert the version number into the tag field
   3. For the release title use “Version <VERSION>”, where `<VERSION>` specifies the version number (e.g. “Version 0.2”)
   4. Click on “Publish Release”

   **Note:** Alternatively you can also use the [`gh`](https://cli.github.com) command:

   ```sh
   gh release create
   ```

   to create the release notes.
