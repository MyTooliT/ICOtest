"""Shared code for all nodes of the ICOtronic system (STU & sensor nodes)"""

# -- Imports ------------------------------------------------------------------

from dynaconf.utils.boxing import DynaBox
from icotronic.can import SensorNode, STU
from semantic_version import Version

# -- Functions ----------------------------------------------------------------


async def check_eeprom_gtin(node: SensorNode | STU, settings: DynaBox):
    """Test if reading and writing the GTIN works

    Args:

        node:
                The node that should be checked

        settings:

                The settings object that contains the GTIN setting

    """

    gtin_written = settings.gtin
    await node.eeprom.write_gtin(gtin_written)
    gtin_read = await node.eeprom.read_gtin()
    assert (
        gtin_written == gtin_read
    ), f"Written GTIN “{gtin_written}” does not match read GTIN “{gtin_read}”"


async def check_eeprom_hardware_version(
    node: SensorNode | STU, settings: DynaBox
):
    """Test if reading and writing the hardware version works

    Args:

        node:
                The node that should be checked

        settings:

                The settings object that contains the hardware version setting

    """

    hardware_version_written = Version.coerce(settings.hardware_version)
    await node.eeprom.write_hardware_version(hardware_version_written)
    hardware_version_read = await node.eeprom.read_hardware_version()
    assert hardware_version_written == hardware_version_read, (
        f"Written hardware version “{hardware_version_written}” does not"
        f"match read hardware version “{hardware_version_read}”"
    )
