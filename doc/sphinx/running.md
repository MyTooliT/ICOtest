# Running Tests

The test for the ICOtronic hardware are based on [pytest]. To execute all the tests for the hardware you can use the following command:

```shell
pytest --pyargs icotest.test
```

after you {ref}`installed <install>` the package. We also provide a CLI tool that more or less acts as a alias for the command above:

```shell
icotest run
```

## Test Groups and GUI Buttons

The GUI mirrors the same workflows as the CLI test groups:

| GUI Button | CLI Test Group | Purpose |
| --- | --- | --- |
| Flash + Rename + Test | `initial` | Flash new firmware, rename the board, then run production tests |
| Flash Only | `flash-only` | Flash firmware only, without renaming or production tests |
| Rename Only | `rename` | Rename a board that still has an old EEPROM name |
| Retest Existing Device | `production` | Run production tests on an already named board |

Use `flash-only` when a board was reflashed but should keep its current EEPROM name, and use `rename` when you only need to recover the name before testing.

To list all available test use the option `--co` or `--collect-only`:

```shell
icotest run --collect-only
```

To execute a specific text you can use the option `-k`, which expects [an expression as argument](https://docs.pytest.org/en/stable/example/markers.html#using-k-expr-to-select-tests-based-on-their-name). For example, let us assume that the collection command above produced the following output:

```text
<Module test_sensor_node.py>
  Test power usage of ICOtronic hardware
  <Coroutine test_connection>
    Test if connection to sensor node is possible
  <Coroutine test_supply_voltage>
    Test if battery voltage is within expected bounds
  <Coroutine test_power_usage_streaming>
    Test power usage of sensor node while streaming
```

In this case we can execute all of the tests of the module `test_sensor_node.py` using the following command:

```shell
icotest run -k test_sensor_node
```

To execute only a single test just add an `and` followed by the test name to the command. For example, to only execute the test `test_supply_voltage` of the module `test_sensor_node.py` use the command:

```shell
icotest run -k "test_sensor_node.py and test_supply_voltage"
```

Another option to execute the same test would be the command:

```shell
icotest run icotest.test.test_sensor_node::test_supply_voltage
```

For more information on how to execute specific tests, please take a look at the [pytest documentation](https://docs.pytest.org/en/stable/usage.html#specifying-tests-selecting-tests).

## Changing Sensor Node Name

While most values used by the tests can only be changed by updating the {ref}`configuration`, we make an exception for the sensor node name. To overwrite this value use the option `-n` or `--name`:

```shell
icotest run --name <sensor_node_name> …
```

## JSON Report

To store data about a test run in a JSON file use the option `--json-report`:

```sh
icotest run --json-report …
```

Tests might also store additional metadata in this JSON file. For example, the test `test_set_base64name` adds the sensor node name to the metadata. If we execute the test with the command:

```sh
icotest run --json-report -k 'sensor_node and base64'
```

and the test finishes successfully, then there should be a file `.report.json` in the current working directory. This file stores the name of the sensor node in an object with the key `Sensor Node Name`. You can print the name using the following [`yq`](https://github.com/mikefarah/yq) command:

```sh
yq '.tests[0].metadata.["Sensor Node Name"]' .report.json
```

## Error Recovery and Resilience

The ICOtest framework is designed to automatically recover from transient hardware communication errors. This improves test reliability by handling temporary STU (Stationary Transceiver Unit) state issues without manual intervention.

### Automatic Error Recovery

The test framework automatically detects and recovers from two types of errors:

**1. Connection Failures**
- **Error**: "Unable to connect to sensor"
- **Trigger**: Occurs when the test cannot establish a connection to a sensor node
- **Recovery**: The framework automatically resets the STU, waits 3 seconds, and retries the connection
- **Result**: Tests continue automatically if the retry succeeds

**2. Data Streaming Disable Failures**
- **Error**: "Unable to disable data streaming"
- **Trigger**: Occurs when the framework cannot properly clean up data streaming from a sensor
- **Recovery**: The framework automatically resets the STU, waits 3 seconds, and retries the operation
- **Result**: Tests continue automatically if the retry succeeds

### What You'll See in Logs

When automatic recovery is triggered, you'll see warning-level log messages indicating:
- What error occurred
- That the STU is being reset
- That the operation will be retried

For example:
```
WARNING: Failed to connect to sensor node 'DeviceName': Unable to connect to sensor. Resetting STU and retrying...
```

or

```
WARNING: Failed to disable data streaming: Unable to disable data streaming. Resetting STU and retrying once...
```

### When Manual Intervention May Be Needed

If errors persist after automatic recovery:
- The test will fail with the original error message
- Check that the STU and sensor hardware are properly connected
- Verify that the sensor node is powered on and within range
- Try running the test again after a longer wait period
- If the problem continues, manually reset the hardware and try again

## Troubleshooting Tests

### Common Error Messages and Solutions

**"Unable to connect to sensor"**
- This error indicates the STU cannot establish communication with the sensor node
- The framework will automatically attempt to recover by resetting the STU and retrying
- If this error persists across multiple test runs:
  - Verify the sensor node is powered on and has a charged battery
  - Check that the sensor is within Bluetooth range of the STU
  - Manually reset the STU by power-cycling it
  - Check for interference from other wireless devices

**"Unable to disable data streaming"**
- This error indicates the STU is in an inconsistent state and cannot properly clean up streaming operations
- The framework will automatically attempt to recover by resetting the STU and retrying
- If this error persists:
  - The STU may need to be manually reset
  - Try rerunning the test after a 30-second delay to allow the STU to fully recover
  - Check that no other applications are communicating with the STU
  - Consider power-cycling the STU if problems continue

### Enabling Verbose Logging for Debugging

If you need to understand more about what's happening during test execution, you can increase the logging level. For example, to output info logging messages (in addition to the warning and error logging messages enabled by default) you can use the `icotest` option `--log` with the argument `info`:

```shell
icotest --log info run
```

The `--log` option supports the [standard log levels](https://docs.python.org/3/library/logging.html#logging-levels):

- `debug` - Very detailed information for diagnosing problems
- `info` - Confirmation that things are working as expected (including error recovery steps)
- `warning` - Indicates an unexpected condition (default level)
- `error` - Error has occurred but recovery is being attempted
- `critical` - A serious error that recovery cannot fix

Using `--log debug` can help identify whether automatic recovery is being triggered and whether it's succeeding.

[pytest]: https://pytest.org
