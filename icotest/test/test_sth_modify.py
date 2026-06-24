"""STH Initial Setup Tests - Firmware Upload and Renaming

These tests must be executed in a specific order:
1. Firmware Upload (order=1)
2. Flash Only (order=1, rename skipped)
3. Set Base64 Name (order=2)
"""

# -- Imports ------------------------------------------------------------------

from logging import getLogger

from pytest import mark

from icotronic.can import STH

from icotest.config import settings
from icotest.test.support.node import check_firmware_upload
from icotest.test.support.mac import convert_mac_base64
from icotest.cli.commander import Commander

# -- Functions ----------------------------------------------------------------


async def _upload_and_reset_firmware():
    """Upload firmware and reset the board to initialize EEPROM."""

    await check_firmware_upload(settings.sensor_node)

    logger = getLogger(__name__)
    logger.info("Resetting device after firmware upload to initialize EEPROM")

    Commander().reset_device()
    logger.info("Device reset complete - EEPROM initialized with defaults")


@mark.order(1)
@mark.initial_setup
async def test_firmware_upload():
    """Upload firmware - MUST be executed FIRST"""

    await _upload_and_reset_firmware()


@mark.order(1)
@mark.initial_firmware_only
async def test_flash_firmware_only(sensor_node_mac_address):
    """Upload firmware only without renaming or additional tests"""

    await _upload_and_reset_firmware()


@mark.order(2)
@mark.initial_setup
async def test_set_base64name(
    sth: STH, sensor_node_mac_address, json_metadata
):
    """Set Sensor Node Name to Base64-encoded MAC address

    This test:
    1. Reads the MAC address of the Sensor Node
    2. Converts it to Base64
    3. Renames the node to this name

    IMPORTANT: Must be executed AFTER test_firmware_upload (order=2)
    """

    logger = getLogger(__name__)

    # Convert MAC address to Base64
    name = convert_mac_base64(sensor_node_mac_address)
    logger.info("Base64-encoded MAC address: %s", name)

    # Rename node using set_name (Bluetooth command)
    await sth.set_name(name)

    # High-visibility output for the operator
    # (logged at WARNING level to ensure visibility)
    banner = "\n" + "*" * 60
    logger.warning(banner)
    logger.warning("DEVICE RENAMED SUCCESSFULLY")
    logger.warning("NEW NAME (BASE64 MAC): %s", name)
    logger.warning("PLEASE WRITE THIS NAME ON THE PCB LABEL!")
    logger.warning(banner)

    # Store name in JSON metadata (for --json-report)
    json_metadata["Sensor Node Name"] = name
    logger.info("Name stored in JSON metadata")
