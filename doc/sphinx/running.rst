*************
Running Tests
*************

.. _pytest: https://pytest.org

The test for the ICOtronic hardware are based on `pytest`_. To execute all the tests for the hardware you can use the following command:

.. code-block:: shell

  pytest --pyargs icotest.test

after you :ref:`installed <install>` the package. To list all available test use the option ``--co`` or ``--collect-only``:

.. code-block:: shell

  pytest --pyargs icotest.test --collect-only

To execute a specific text you can use the option ``-k``, which expects `an expression as argument <https://docs.pytest.org/en/stable/example/markers.html#using-k-expr-to-select-tests-based-on-their-name>`__. For example, let us assume that the collection command command above produced the following output:

.. code-block:: text

   <Module test_sensor_node.py>
     Test power usage of ICOtronic hardware
     <Coroutine test_connection>
       Test if connection to sensor node is possible
     <Coroutine test_supply_voltage>
       Test if battery voltage is within expected bounds
     <Coroutine test_power_usage_streaming>
       Test power usage of sensor node while streaming

In this case we can execute all of the tests of the module ``test_sensor_node.py`` using the following command:

.. code-block:: shell

  pytest --pyargs icotest.test -k test_sensor_node

To execute only a single test just add an ``and`` followed by the test name to the command. For example, to only execute the test ``test_supply_voltage`` of the module ``test_sensor_node.py`` use the command:

.. code-block:: shell

  pytest --pyargs icotest.test -k "pytest --pyargs icotest.test and test_supply_voltage"

Another option to execute the same test would be the command:

.. code-block:: shell

  pytest --pyargs icotest.test icotest.test.test_sensor_node::test_supply_voltage

For more information on how to execute specific tests, please take a look at the `pytest documentation <https://docs.pytest.org/en/stable/usage.html#specifying-tests-selecting-tests>`__.
