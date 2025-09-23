# -- Imports ------------------------------------------------------------------

from asyncio import Event, run, TaskGroup, to_thread
from logging import getLogger

from icotronic.can import SensorNode, StreamingConfiguration
from icotronic.cmdline.commander import Commander

# -- Functions ----------------------------------------------------------------


async def test_power_usage_streaming(
    sensor_node: SensorNode, serial_number: int, chip: str
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
        commander = Commander(serial_number=serial_number, chip=chip)
        return commander.read_power_usage()

    started_streaming = Event()

    async with TaskGroup() as task_group:
        stream_data_task = task_group.create_task(
            stream_data(started_streaming)
        )
        await started_streaming.wait()
        read_power_task = task_group.create_task(to_thread(read_power_usage))
        power_usage = await read_power_task
        getLogger().info(f"Streaming power usage: {power_usage} mW")
        stream_data_task.cancel()

    assert 40 <= power_usage <= 60
