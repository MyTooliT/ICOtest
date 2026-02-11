"""Shared code for all nodes of the ICOtronic system (STU & sensor nodes)"""

# -- Imports ------------------------------------------------------------------

from asyncio import sleep
from logging import getLogger
from math import isclose
from operator import __eq__
from pathlib import Path
from typing import Callable, TypeVar

from dynaconf.utils.boxing import DynaBox
from icotronic.can import SensorNode, STH, STU
from icotronic.can.node.eeprom.status import EEPROMStatus
from icotronic.can.status import State
from semantic_version import Version

from icotest.cli.commander import Commander

# -- Types --------------------------------------------------------------------

EEPROMValue = TypeVar("EEPROMValue", Version, str)
"""Type of an object that can be written into EEPROM"""

# -- Functions ----------------------------------------------------------------


async def check_firmware_upload(node_settings: DynaBox):
    """Upload firmware"""

    firmware_locations = node_settings.firmware.locations

    logger = getLogger(__name__)
    logger.debug("Firmware locations: %s", firmware_locations)
    image_filepaths: list[Path] = []
    for firmware_location in firmware_locations:
        image_filepath = Path(firmware_location).expanduser().resolve()
        if not image_filepath.exists():
            raise FileNotFoundError(
                "Firmware file {image_filepath} does not exist"
            )
        if not image_filepath.is_file():
            raise FileNotFoundError(
                f"Firmware file {image_filepath} is not a file"
            )
        image_filepaths.append(image_filepath)

    chip = node_settings.firmware.chip
    Commander().upload_flash(chip=chip, filepaths=image_filepaths)


async def check_connection(node: SensorNode | STU) -> None:
    """Check connection to node

    Args:

        node:

            The node for that should be checked

    """

    await sleep(1)  # Wait for startup of sensor node

    # Just send a request for the state and check, if the result
    # matches our expectations.
    state = await node.get_state()

    expected_state = State(
        mode="Get", location="Application", state="Operating"
    )

    assert state == expected_state, (
        (
            f"Expected state “{expected_state}” does not match "
            f"received state “{state}”"
        ),
    )


async def check_write_read_eeprom_function(
    node: SensorNode | STH | STU,
    name: str,
    written: EEPROMValue,
    comparator: Callable[[EEPROMValue, EEPROMValue], bool],
    description: str,
):
    """Check a written and read EEPROM value for relation to each other

    Args:

        node:
                The node that should be checked

        name:

                The name of the EEPROM value

        written:

                The value that should be written and then read afterwards

        comparator:

                The function that will be applied to check if the values are
                related or not

        description:

                A text that describes the **inverse** of the comparator
                function; e.g. for something like the function ``__eq__`` this
                could be something like ``"is not equal to"``.

    """

    function_name = name.lower().replace(" ", "_")
    write_coroutine = getattr(node.eeprom, f"write_{function_name}")
    read_coroutine = getattr(node.eeprom, f"read_{function_name}")
    await write_coroutine(written)
    read = await read_coroutine()
    logger = getLogger(__name__)
    logger.debug("Type of written value: %s", type(written))
    logger.debug("Type of read value: %s", type(read))
    assert comparator(
        written, read
    ), f"Written {name} “{written}” {description} read {name} “{read}”"


async def check_write_read_eeprom(
    node: SensorNode | STH | STU, name: str, written: EEPROMValue
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

    return await check_write_read_eeprom_function(
        node, name, written, __eq__, "does not match"
    )


async def check_write_read_eeprom_close(
    node: SensorNode | STH | STU, name: str, written: float
) -> None:
    """Check that a written and read EEPROM value are approximately the same

    Args:

        node:
                The node that should be checked

        name:

                The name of the EEPROM value

        written:

                The value that should be written and then read afterwards

    """

    return await check_write_read_eeprom_function(
        node, name, written, isclose, "is not close to"
    )


async def check_eeprom_product_data(node: SensorNode | STU, settings: DynaBox):
    """Test if reading and writing EEPROM product data works

    Args:

        node:

            The node that should be checked

        settings:

            The settings object that contains the node setting

    """

    await check_write_read_eeprom(node, "GTIN", settings.gtin)
    await check_write_read_eeprom(
        node, "hardware version", Version.coerce(settings.hardware_version)
    )
    # I am not sure, if the firmware already inits the EEPROM with the firmware
    # version. Writing back the same firmware version into the EEPROM should
    # not be a problem though.
    await check_write_read_eeprom(
        node, "firmware version", await node.get_firmware_version()
    )
    # Originally we assumed that this value would be set by the
    # firmware itself. However, according to tests with an empty EEPROM
    # this is not the case.
    await check_write_read_eeprom(
        node, "release name", settings.firmware.release_name
    )
    await check_write_read_eeprom(
        node, "serial number", settings.serial_number
    )
    await check_write_read_eeprom(node, "product name", settings.product_name)
    await check_write_read_eeprom(node, "OEM data", settings.oem_data)


async def check_eeprom_statistics(node: SensorNode | STU, settings: DynaBox):
    """Test if reading and writing EEPROM statistic data works

    Args:

        node:

            The node that should be checked

        settings:

            The settings object that contains the node setting

    """

    for attribute in (
        "power on cycles",
        "power off cycles",
        "operating time",
        "under voltage counter",
        "watchdog reset counter",
    ):
        await check_write_read_eeprom(node, attribute, 0)

    await check_write_read_eeprom(
        node, "production date", settings.production_date
    )
    await check_write_read_eeprom(node, "batch number", settings.batch_number)


async def check_eeprom_status(node: SensorNode | STU):
    """Test if reading and writing the EEPROM status byte works

    Args:

        node:

            The node that should be checked

    """

    await check_write_read_eeprom(node, "status", EEPROMStatus("Initialized"))
