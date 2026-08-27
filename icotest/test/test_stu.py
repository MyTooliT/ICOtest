"""Test STU"""

# -- Imports ------------------------------------------------------------------

from pytest import mark

from icotronic.can import STU

from icotest.config import settings
from icotest.test.support.node import (
    check_firmware_upload,
    check_connection,
    check_eeprom_product_data,
    check_eeprom_statistics,
    check_eeprom_status,
)

# -- Functions ----------------------------------------------------------------


@mark.stu
async def test_firmware_upload():
    """Upload firmware for STU (separate from sensor node initial setup)"""

    await check_firmware_upload(settings.stu)


@mark.stu
@mark.basic
async def test_connection(stu: STU):
    """Test if connection to STU is possible"""

    await check_connection(stu)


@mark.stu
@mark.basic
async def test_eeprom(stu: STU):
    "Test if reading and writing of EEPROM values works"

    await check_eeprom_product_data(stu, settings.stu)
    await check_eeprom_statistics(stu, settings.stu)
    await check_eeprom_status(stu)
