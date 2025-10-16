"""Test STU"""

# -- Imports ------------------------------------------------------------------

from logging import getLogger

from icotronic.can import Connection, STU
from icotronic.can.error import CANInitError

from icotest.config import settings
from icotest.firmware import upload_flash
from icotest.test.node import (
    check_eeprom_product_data,
    check_eeprom_statistics,
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


async def test_eeprom(stu: STU):
    "Test if reading and writing of EEPROM values works"

    await check_eeprom_product_data(stu, settings.stu)
    await check_eeprom_statistics(stu)
