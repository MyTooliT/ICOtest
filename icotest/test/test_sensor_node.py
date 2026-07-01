"""Test sensor node hardware (SHA, STH, SMH…)"""

# -- Imports ------------------------------------------------------------------

from asyncio import Event, TaskGroup, to_thread
from logging import getLogger

from pytest import mark

from icotronic.can import SensorNode, StreamingConfiguration, STU

from icotest.cli.commander import Commander
from icotest.config import settings
from icotest.test.support.common import check_power_usage
from icotest.test.support.node import (
    check_connection,
    check_eeprom_product_data,
    check_eeprom_statistics,
    check_eeprom_status,
)
from icotest.test.support.sensor_node import (
    check_eeprom_name,
    check_eeprom_bluetooth_times,
)

# -- Functions ----------------------------------------------------------------


# Order 10-19: Basic Tests


@mark.order(10)
@mark.basic
async def test_connection(sensor_node: SensorNode):
    """Test if connection to sensor node is possible"""

    await check_connection(sensor_node)


@mark.order(11)
@mark.basic
async def test_supply_voltage(sensor_node: SensorNode, json_metadata: dict):
    """Test if battery voltage is within expected bounds"""

    supply_voltage = await sensor_node.get_supply_voltage()
    expected_voltage = settings.sensor_node.supply.voltage.average
    tolerance_voltage = settings.sensor_node.supply.voltage.tolerance

    expected_minimum_voltage = expected_voltage - tolerance_voltage
    expected_maximum_voltage = expected_voltage + tolerance_voltage

    # Store in JSON report
    json_metadata["record"](
        "supply_voltage",
        supply_voltage,
        unit="V",
        lower=expected_minimum_voltage,
        upper=expected_maximum_voltage,
        description="Battery/supply voltage of the sensor node",
    )

    assert supply_voltage >= expected_minimum_voltage, (
        f"Supply voltage of {supply_voltage:.3f} V is lower "
        "than expected minimum voltage of "
        f"{expected_minimum_voltage:.3f} V"
    )
    assert supply_voltage <= expected_maximum_voltage, (
        f"Supply voltage of {supply_voltage:.3f} V is "
        "greater than expected maximum voltage of "
        f"{expected_minimum_voltage:.3f} V"
    )


# Order 20-29: Power Tests


@mark.order(20)
@mark.power
async def test_power_usage_disconnected(
    stu: STU,  # pylint: disable=unused-argument
    json_metadata: dict,
) -> None:
    """Check power usage in disconnected state"""

    commander = Commander()
    commander.enable_debug_mode()
    power_usage_mw = commander.read_power_usage()
    getLogger(__name__).info("Disconnected power usage: %s mW", power_usage_mw)

    limit = settings.sensor_node.power.disconnected

    # Store in JSON report
    json_metadata["record"](
        "power_usage_disconnected",
        power_usage_mw,
        unit="mW",
        upper=limit,
        description="Power usage when not connected to STU",
    )
    json_metadata["failure_analysis"] = (
        "High power draw may indicate a short circuit, "
        "a faulty LDO, or poor soldering quality."
    )

    await check_power_usage(power_usage_mw, limit)


@mark.order(21)
@mark.power
async def test_power_usage_connected(
    sensor_node: SensorNode,  # pylint: disable=unused-argument
    json_metadata: dict,
) -> None:
    """Check power usage in connected state"""

    commander = Commander()
    commander.enable_debug_mode()
    power_usage_mw = commander.read_power_usage()
    getLogger(__name__).info("Connected power usage: %s mW", power_usage_mw)

    limit = settings.sensor_node.power.connected

    # Store in JSON report
    json_metadata["record"](
        "power_usage_connected",
        power_usage_mw,
        unit="mW",
        upper=limit,
        description="Power usage when connected to STU",
    )
    json_metadata["failure_analysis"] = (
        "High power draw often suggests internal component issues "
        "or active sub-modules drawing unexpected current."
    )

    await check_power_usage(power_usage_mw, limit)


@mark.order(22)
@mark.power
async def test_power_usage_streaming(
    sensor_node: SensorNode, json_metadata: dict
):
    """Test power usage of sensor node while streaming"""

    async def stream_data(started_streaming: Event) -> None:
        async with sensor_node.open_data_stream(
            StreamingConfiguration(first=True)
        ) as stream:
            async for _ in stream:
                if not started_streaming.is_set():
                    started_streaming.set()

    def read_power_usage() -> float:
        return Commander().read_power_usage()

    started_streaming = Event()

    async with TaskGroup() as task_group:
        stream_data_task = task_group.create_task(
            stream_data(started_streaming)
        )
        await started_streaming.wait()
        read_power_task = task_group.create_task(to_thread(read_power_usage))
        power_usage_mw = await read_power_task
        getLogger(__name__).info(
            "Streaming power usage: %s mW", power_usage_mw
        )
        stream_data_task.cancel()

    limit = settings.sensor_node.power.streaming

    # Store in JSON report
    json_metadata["record"](
        "power_usage_streaming",
        power_usage_mw,
        unit="mW",
        upper=limit,
        description="Power usage during active data transmission",
    )
    json_metadata["failure_analysis"] = (
        "High streaming power may indicate RF hardware issues or over-active"
        " sensors."
    )

    await check_power_usage(power_usage_mw, limit)


@mark.order(12)
@mark.basic
async def test_eeprom(sensor_node: SensorNode):
    "Test if reading and writing of EEPROM values works"

    await check_eeprom_name(sensor_node, settings.sensor_node)
    await check_eeprom_product_data(sensor_node, settings.sensor_node)
    await check_eeprom_statistics(sensor_node, settings.sensor_node)
    await check_eeprom_status(sensor_node)
    await check_eeprom_bluetooth_times(sensor_node, settings.sensor_node)


# moved test_set_base64name to test_sth_modify.py
