"""Test STU"""

# -- Imports ------------------------------------------------------------------

from logging import getLogger

from icotronic.can.status import State
from icotronic.can import Connection, STU

from icotest.config import settings
from icotest.firmware import upload_flash
from icotest.test.node import (
    check_eeprom_product_data,
    check_eeprom_statistics,
    check_eeprom_status,
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

    async with Connection() as stu:
        # Just send a request for the state and check, if the result
        # matches our expectations.
        state = await stu.get_state()

        expected_state = State(
            mode="Get", location="Application", state="Operating"
        )

        assert state == expected_state, (
            (
                f"Expected state “{expected_state}” does not match "
                f"received state “{state}”"
            ),
        )


async def test_eeprom(stu: STU):
    "Test if reading and writing of EEPROM values works"

    await check_eeprom_product_data(stu, settings.stu)
    await check_eeprom_statistics(stu, settings.stu)
    await check_eeprom_status(stu)
