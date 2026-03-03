# Development

## Requirements

While not strictly required we assume that you installed [`just`][just] in the description below.

## Install

### uv

We recommend you use [`uv`](https://docs.astral.sh/uv) to install
the package. To do that please use the following commands in the root of
the repository:

```shell
uv venv --allow-existing
uv sync --all-extras
```

**Note:** If you use the install option above, then you need to prefix
all commands with `uv run`. For example instead of `pytest` use
the command `uv run pytest`.

### Pip

To install the package

- in development/editable mode
- including development (`dev`) packages

please use the following command in the root of the repository:

```shell
pip install -e .[dev]
```

#### Uninstall

```shell
pip uninstall icotest
```

## Release

**Note:** In the text below we assume that you want to release version
`<VERSION>` of the package. Please just replace this version number
with the version that you want to release (e.g. `0.2.0`).

1. Make sure that all the checks and tests work correctly locally

   ```shell
   just
   ```

2. Make sure that installing the package with `pip` works:

   ```shell
   pip install -e .
   icotest run -k 'stu and test_connection'
   pip uninstall -y icotest
   ```

3. Make sure all [workflows of the CI system work
   correctly](https://github.com/MyTooliT/ICOtest/actions)

4. Check that the most recent [“Read the Docs” build of the
   documentation ran
   successfully](https://app.readthedocs.org/projects/icotest/)

5. Release a new version on
   [PyPI](https://pypi.org/project/icotest/):
   1. Increase version number
   2. Add git tag containing version number
   3. Push changes

   ```shell
   just release <VERSION>
   ```

5) Open the [release
   notes](https://github.com/MyTooliT/ICOtest/tree/main/doc/release)
   for the latest version and [create a new
   release](https://github.com/MyTooliT/ICOtest/releases/new)
   1. Paste them into the main text of the release web page
   2. Insert the version number into the tag field
   3. For the release title use “Version ”, where `<VERSION>`
      specifies the version number (e.g. “Version 0.2”)
   4. Click on “Publish Release”

   **Note:** Alternatively you can also use the
   [gh] CLI command:

   ```shell
   gh release create
   ```

   to create the release notes.

[gh]: https://cli.github.com
[just]: https://github.com/casey/just
