"""Test STU"""

# -- Imports ------------------------------------------------------------------

from logging import getLogger

from icotronic.can import Connection, STU
from icotronic.can.error import CANInitError
from semantic_version import Version

from icotest.config import settings
from icotest.firmware import upload_flash
from icotest.test.node import check_eeprom_gtin

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

    hardware_version_written = Version.coerce(settings.stu.hardware_version)
    await stu.eeprom.write_hardware_version(hardware_version_written)
    hardware_version_read = await stu.eeprom.read_hardware_version()
    assert hardware_version_written == hardware_version_read, (
        f"Written hardware version “{hardware_version_written}” does not"
        f"match read hardware version “{hardware_version_read}”"
    )


async def test_eeprom_firmware_version(stu: STU):
    """Test if reading and writing the firmware version works"""

    # I am not sure, if the firmware already inits the EEPROM with the firmware
    # version. Writing back the same firmware version into the EEPROM should
    # not be a problem though.
    firmware_version_written = await stu.get_firmware_version()
    await stu.eeprom.write_firmware_version(firmware_version_written)
    firmware_version_read = await stu.eeprom.read_firmware_version()
    assert firmware_version_written == firmware_version_read, (
        (
            f"Written firmware version “{firmware_version_written}” does not "
            f"match read firmware version “{firmware_version_read}”"
        ),
    )
