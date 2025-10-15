"""Test STU"""

# -- Imports ------------------------------------------------------------------

from logging import getLogger

from icotronic.can import Connection, STU
from icotronic.can.error import CANInitError


from icotest.config import settings
from icotest.firmware import upload_flash

# -- Functions ----------------------------------------------------------------


async def test_firmware():
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

    gtin = settings.stu.gtin
    await stu.eeprom.write_gtin(gtin)
    read_gtin = await stu.eeprom.read_gtin()
    assert (
        gtin == read_gtin
    ), f"Written GTIN “{gtin}” does not match read GTIN “{read_gtin}”"
