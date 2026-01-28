"""Test sensor node hardware (SHA, STH, SMH…)"""

# -- Imports ------------------------------------------------------------------

from asyncio import Event, TaskGroup, to_thread
from logging import getLogger

from icotronic.can import SensorNode, StreamingConfiguration, STU

from icotest.cli.commander import Commander
from icotest.config import settings
from icotest.test.support.common import check_power_usage
from icotest.test.support.mac import convert_mac_base64
from icotest.test.support.node import (
    check_connection,
    check_firmware_upload,
    check_eeprom_product_data,
    check_eeprom_statistics,
    check_eeprom_status,
)
from icotest.test.support.sensor_node import (
    check_eeprom_name,
    check_eeprom_bluetooth_times,
)

# -- Functions ----------------------------------------------------------------


async def test_firmware_upload():
    """Upload firmware"""

    await check_firmware_upload(settings.sensor_node)


async def test_connection(sensor_node: SensorNode):
    """Test if connection to sensor node is possible"""

    await check_connection(sensor_node)


async def test_set_base64name(sensor_node: SensorNode, capsys, json_metadata):
    """Set name to Base64 encoded MAC address of sensor node"""

    mac_address = await sensor_node.get_mac_address()
    getLogger().info("MAC address: %s", mac_address)
    name = convert_mac_base64(mac_address)
    with capsys.disabled():
        print(f"Base64 encoded MAC address (Bluetooth name): {name}")
    json_metadata["Sensor Node Name"] = name

    await sensor_node.set_name(name)


async def test_supply_voltage(sensor_node: SensorNode):
    """Test if battery voltage is within expected bounds"""

    supply_voltage = await sensor_node.get_supply_voltage()
    expected_voltage = settings.sensor_node.supply.voltage.average
    tolerance_voltage = settings.sensor_node.supply.voltage.tolerance

    expected_minimum_voltage = expected_voltage - tolerance_voltage
    expected_maximum_voltage = expected_voltage + tolerance_voltage

    assert supply_voltage >= expected_minimum_voltage, (
        (
            f"Supply voltage of {supply_voltage:.3f} V is lower "
            "than expected minimum voltage of "
            f"{expected_minimum_voltage:.3f} V"
        ),
    )
    assert supply_voltage <= expected_maximum_voltage, (
        (
            f"Supply voltage of {supply_voltage:.3f} V is "
            "greater than expected maximum voltage of "
            f"{expected_minimum_voltage:.3f} V"
        ),
    )


async def test_power_usage_disconnected(
    stu: STU,  # pylint: disable=unused-argument
) -> None:
    """Check power usage in disconnected state"""

    commander = Commander()
    commander.enable_debug_mode()
    power_usage_mw = commander.read_power_usage()
    getLogger(__name__).info("Disconnected power usage: %s mW", power_usage_mw)

    await check_power_usage(
        power_usage_mw, settings.sensor_node.power.disconnected
    )


async def test_power_usage_connected(
    sensor_node: SensorNode,  # pylint: disable=unused-argument
) -> None:
    """Check power usage in connected state"""

    commander = Commander()
    commander.enable_debug_mode()
    power_usage_mw = commander.read_power_usage()
    getLogger(__name__).info("Connected power usage: %s mW", power_usage_mw)

    await check_power_usage(
        power_usage_mw, settings.sensor_node.power.connected
    )


async def test_power_usage_streaming(sensor_node: SensorNode):
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

    await check_power_usage(
        power_usage_mw, settings.sensor_node.power.streaming
    )


async def test_eeprom(sensor_node: SensorNode):
    "Test if reading and writing of EEPROM values works"

    await check_eeprom_name(sensor_node, settings.sensor_node)
    await check_eeprom_product_data(sensor_node, settings.sensor_node)
    await check_eeprom_statistics(sensor_node, settings.sensor_node)
    await check_eeprom_status(sensor_node)
    await check_eeprom_bluetooth_times(sensor_node, settings.sensor_node)
