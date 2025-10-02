"""Test power usage of ICOtronic hardware"""

# -- Imports ------------------------------------------------------------------

from asyncio import Event, TaskGroup, to_thread
from logging import getLogger

from icotronic.can import SensorNode, StreamingConfiguration, STU
from icotronic.cmdline.commander import Commander

from icotest.config import settings

# -- Functions ----------------------------------------------------------------


async def test_connection(stu: STU, sensor_node_name: str):
    """Test if connection to sensor node is possible"""

    async with stu.connect_sensor_node(sensor_node_name):
        assert (
            True
        ), f"Unable to connect to sensor node with name “{sensor_node_name}”"


async def test_battery_voltage(sensor_node: SensorNode):
    """Test if battery voltage is within expected bounds"""

    supply_voltage = await sensor_node.get_supply_voltage()
    expected_voltage = settings.sensor_node.battery_voltage.average
    tolerance_voltage = settings.sensor_node.battery_voltage.tolerance

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
        power_usage = await read_power_task
        getLogger().info("Streaming power usage: %s mW", power_usage)
        stream_data_task.cancel()

    minimum_power = 40
    maximum_power = 60
    assert minimum_power <= power_usage, (
        f"Power usage of {power_usage} mW smaller than expected minimum of "
        f"{minimum_power} mW"
    )
    assert power_usage <= maximum_power, (
        f"Power usage of {power_usage} mW larger than expected maximum of "
        f"{maximum_power} mW"
    )
