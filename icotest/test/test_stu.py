"""Test STU"""

# -- Imports ------------------------------------------------------------------

from logging import getLogger

from icotronic.can import Connection, STU
from icotronic.can.error import CANInitError

from icotest.config import settings
from icotest.firmware import upload_flash
from icotest.test.node import (
    check_eeprom_firmware_version,
    check_eeprom_gtin,
    check_eeprom_hardware_version,
)

# -- Functions ----------------------------------------------------------------


async def test_firmware_upload():
    """Upload firmware"""

    logger = getLogger(__name__)
    firmware_location = settings.stu.firmware.location
    logger.info("Firmware Location: %s", firmware_location)

    chip = settings.stu.firmware.chip
    upload_flash(chip, firmware_location)


async def test_connection():
    """Test if connection to STU is possible"""

    message = "Unable to connect to STU"

    try:
        async with Connection():
            assert True, message
    except CANInitError:
        assert False, message


async def test_eeprom_gtin(stu: STU):
    """Test if reading and writing the GTIN works"""

    await check_eeprom_gtin(stu, settings.stu)


async def test_eeprom_hardware_version(stu: STU):
    """Test if reading and writing the hardware version works"""

    await check_eeprom_hardware_version(stu, settings.stu)


async def test_eeprom_firmware_version(stu: STU):
    """Test if reading and writing the firmware version works"""

    await check_eeprom_firmware_version(stu)
