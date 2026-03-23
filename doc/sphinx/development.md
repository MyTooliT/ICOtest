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

## Error Recovery Patterns

The ICOtest framework implements automatic error recovery for transient hardware communication issues. When developing new tests or features, you should understand these patterns to maintain consistency and reliability.

### Connection Failure Recovery Pattern

**Location**: `icotest/test/conftest.py` - `_connect_with_retry()` function

**Pattern**: When the framework attempts to connect to a sensor node:

1. Try to establish the connection
2. If "Unable to connect to sensor" error occurs:
   - Log a warning message
   - Reset the STU via `await stu.reset()`
   - Wait 3 seconds: `await asyncio.sleep(3)`
   - Retry the connection exactly once
3. If any other error occurs, re-raise it immediately

**When to Use**: Use the `sensor_node` or `sth` fixtures in your tests. These fixtures already implement this pattern automatically through the `_connect_with_retry()` helper function.

**Example**:
```python
async def test_my_feature(sensor_node: SensorNode):
    # Connection errors are automatically recovered
    # No additional error handling needed
    await sensor_node.some_operation()
```

### Data Streaming Disable Error Recovery Pattern

**Location**: `icotest/test/support/sensor_node.py` - `read_streaming_data()` function

**Pattern**: When the framework collects streaming data from a sensor:

1. Open a data stream and collect measurements
2. If "Unable to disable data streaming" error occurs during cleanup:
   - Log a warning message with the original error
   - Reset the STU via `await stu.reset()`
   - Wait 3 seconds: `await asyncio.sleep(3)`
   - Retry the streaming operation exactly once
3. If any other error occurs, re-raise it immediately
4. Return the collected measurement data

**When to Use**: When you need to collect streaming data from a sensor in your tests, pass the `stu` fixture to the `read_streaming_data()` function.

**Example**:
```python
async def test_acceleration(sth: STH, stu: STU):
    config = StreamingConfiguration(first=True)
    # Pass stu to enable automatic recovery
    measurement_data = await read_streaming_data(
        sth, config, length=100, stu=stu
    )
```

### Implementing Similar Recovery

If you need to implement error recovery in other parts of the framework:

1. **Identify the error condition**: Determine what error message indicates a transient STU state issue
2. **Wrap in try-except**: Catch the specific error condition
3. **Reset and retry**: Reset the STU and wait 3 seconds before retrying
4. **Limit retries**: Only retry once to avoid infinite loops
5. **Log appropriately**: Use `getLogger().warning()` to document recovery attempts
6. **Re-raise other errors**: Don't suppress errors unrelated to the transient condition

**Recovery Template**:
```python
try:
    # Attempt operation
    await perform_operation()
except TimeoutError as e:
    if "specific error message" in str(e):
        logger = getLogger(__name__)
        logger.warning(
            "Error occurred: %s. Resetting STU and retrying...", e
        )
        await stu.reset()
        await asyncio.sleep(3)
        # Retry exactly once
        await perform_operation()
    else:
        raise
```

### Best Practices

- **Always pass STU when needed**: Functions that might encounter transient errors should accept an optional `stu` parameter
- **Document recovery behavior**: Include information about recovery in function docstrings
- **Use consistent logging**: Follow the existing pattern of warning-level logs for recovery attempts
- **Don't suppress unexpected errors**: Only handle the specific transient errors you expect
- **Test recovery logic**: When adding new recovery code, test both success and failure paths

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

6. Open the [release
   notes](https://github.com/MyTooliT/ICOtest/tree/main/doc/release)
   for the latest version and [create a new
   release](https://github.com/MyTooliT/ICOtest/releases/new)
   1. Paste them into the main text of the release web page
   2. Insert the version number into the tag field
   3. For the release title use “Version `<VERSION>`” (e.g. “Version 0.2”)
   4. Click on “Publish Release”

   **Note:** Alternatively you can also use the
   [gh] CLI command:

   ```shell
   gh release create
   ```

   to create the release notes.

[gh]: https://cli.github.com
[just]: https://github.com/casey/just
