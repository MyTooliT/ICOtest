"""Shared code for all sensor nodes of the ICOtronic system"""

# -- Imports ------------------------------------------------------------------

import asyncio
from logging import getLogger

from dynaconf.utils.boxing import DynaBox
from icotronic.can import SensorNode, StreamingConfiguration, STU
from icotronic.can.error import ErrorResponseError, NoResponseError
from icotronic.can.streaming.error import StreamingTimeoutError
from icotronic.measurement import MeasurementData

from icotest.test.support.node import check_write_read_eeprom

# -- Functions ----------------------------------------------------------------


async def check_eeprom_name(node: SensorNode, settings: DynaBox):
    """Test if reading and writing the name into the EEPROM works

    Args:

        node:

            The sensor node that should be checked

        settings:

            The settings object that contains the sensor node setting

    """

    await check_write_read_eeprom(node, "name", settings.name)


async def check_eeprom_bluetooth_times(node: SensorNode, settings: DynaBox):
    """Test if reading and writing the Bluetooth times works

    Args:

        node:

            The sensor node that should be checked

        settings:

            The settings object that contains the sensor node setting

    """

    bluetooth = settings.bluetooth

    await check_write_read_eeprom(
        node, "advertisement time 1", bluetooth.advertisement_time_1
    )
    await check_write_read_eeprom(node, "sleep time 1", bluetooth.sleep_time_1)
    await check_write_read_eeprom(
        node, "advertisement time 2", bluetooth.advertisement_time_2
    )
    await check_write_read_eeprom(node, "sleep time 2", bluetooth.sleep_time_2)


async def read_streaming_data(
    node: SensorNode,
    config: StreamingConfiguration,
    length: int,
    stu: STU | None = None,
) -> MeasurementData:
    """Collect a certain number of streaming data (messages)

    Args:

        node:

            The sensor node where streaming data should be collected

        config:

            The streaming configuration that should be used to collect data

        length:

            The amount of streaming data stored in the returned measurement

        stu:
            Optional STU connection for automatic recovery on streaming
            errors (timeout, ADC config read, disable failures)

    Returns:

        A measurement storing ``length`` streaming messages

    Raises:

        Exception: Re-raised if CAN error is not recoverable or if STU
            recovery fails after one retry

    """
    logger = getLogger(__name__)

    measurement_data = MeasurementData(config)
    for attempt in range(2):
        measurement_data = MeasurementData(config)
        try:
            async with node.open_data_stream(config) as stream:
                async for data, _ in stream:
                    measurement_data.append(data)
                    if len(measurement_data) >= length:
                        break

            return measurement_data

        except (StreamingTimeoutError, NoResponseError, ErrorResponseError) as e:
            if stu is None or attempt >= 1:
                raise

            logger.warning(
                "CAN communication error during streaming: %s. "
                "Resetting STU and retrying once...",
                e,
            )

            await stu.reset()
            await asyncio.sleep(3)

    return measurement_data
