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


async def check_eeprom_firmware_version(node: SensorNode):
    """Test if reading and writing the firmware version works

    Args:

        node:
                The node that should be checked

    """

    # I am not sure, if the firmware already inits the EEPROM with the firmware
    # version. Writing back the same firmware version into the EEPROM should
    # not be a problem though.
    firmware_version_written = await node.get_firmware_version()
    await node.eeprom.write_firmware_version(firmware_version_written)
    firmware_version_read = await node.eeprom.read_firmware_version()
    assert firmware_version_written == firmware_version_read, (
        (
            f"Written firmware version “{firmware_version_written}” does not "
            f"match read firmware version “{firmware_version_read}”"
        ),
    )


async def check_eeprom_product_data(node: SensorNode | STU, settings: DynaBox):
    """Test if reading and writing EEPROM product data works

    Args:

        node:
                The node that should be checked

        settings:

                The settings object that contains the node setting

    """

    for check in (
        check_eeprom_gtin,
        check_eeprom_hardware_version,
    ):
        await check(node, settings)
    await check_eeprom_firmware_version(node)
