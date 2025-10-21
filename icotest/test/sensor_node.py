"""Shared code for all sensor nodes of the ICOtronic system"""

# -- Imports ------------------------------------------------------------------

from dynaconf.utils.boxing import DynaBox
from icotronic.can import SensorNode

from icotest.test.node import check_write_read_eeprom

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
