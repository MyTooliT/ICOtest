# Running Tests

The test for the ICOtronic hardware are based on [pytest]. To execute all the tests for the hardware you can use the following command:

```shell
pytest --pyargs icotest.test
```

after you {ref}`installed <install>` the package. We also provide a CLI tool that more or less acts as a alias for the command above:

```shell
icotest run
```

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

## Debugging Tests

Sometimes you want to get additional information about test execution. For that purpose you can increase the logging level. For example, to output info logging messages (in addition to the warning and error logging messages enabled by default) you can use the `icotest` option `--log` with the argument `info`:

```shell
icotest --log info run
```

The `--log` option supports the [standard log levels](https://docs.python.org/3/library/logging.html#logging-levels):

- `debug`
- `info`
- `warning`
- `error`
- `critical`

[pytest]: https://pytest.org
