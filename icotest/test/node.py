"""Shared code for all nodes of the ICOtronic system (STU & sensor nodes)"""

# -- Imports ------------------------------------------------------------------

from typing import TypeVar

from dynaconf.utils.boxing import DynaBox
from icotronic.can import SensorNode, STU
from semantic_version import Version

# -- Types --------------------------------------------------------------------

EEPROMValue = TypeVar("EEPROMValue", Version, str)
"""Type of an object that can be written into EEPROM"""

# -- Functions ----------------------------------------------------------------


async def check_write_read(
    node: SensorNode | STU, name: str, written: EEPROMValue
) -> None:
    """Check that a written and read EEPROM value match

    Args:

        node:
                The node that should be checked

        name:

                The name of the EEPROM value

        written:

                The value that should be written and then read afterwards

    """

    function_name = name.lower().replace(" ", "_")
    write_coroutine = getattr(node.eeprom, f"write_{function_name}")
    read_coroutine = getattr(node.eeprom, f"read_{function_name}")
    await write_coroutine(written)
    read = await read_coroutine()
    assert (
        written == read
    ), f"Written {name} “{written}” does not match read {name} “{read}”"


async def check_eeprom_product_data(node: SensorNode | STU, settings: DynaBox):
    """Test if reading and writing EEPROM product data works

    Args:

        node:
                The node that should be checked

        settings:

                The settings object that contains the node setting

    """

    await check_write_read(node, "GTIN", settings.gtin)
    await check_write_read(
        node, "hardware version", Version.coerce(settings.hardware_version)
    )
    # I am not sure, if the firmware already inits the EEPROM with the firmware
    # version. Writing back the same firmware version into the EEPROM should
    # not be a problem though.
    await check_write_read(
        node, "firmware version", await node.get_firmware_version()
    )
