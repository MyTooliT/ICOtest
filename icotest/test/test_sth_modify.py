"""STH Initial Setup Tests - Firmware Upload and Renaming

These tests must be executed in a specific order:
1. Firmware Upload (order=1)
2. Set Base64 Name (order=2)
"""

# -- Imports ------------------------------------------------------------------

from logging import getLogger

from pytest import mark

from icotronic.can import STH

from icotest.config import settings
from icotest.test.support.node import check_firmware_upload
from icotest.test.support.mac import convert_mac_base64

# -- Functions ----------------------------------------------------------------


@mark.order(1)
@mark.initial_setup
async def test_firmware_upload():
    """Upload firmware - MUST be executed FIRST"""

    await check_firmware_upload(settings.sensor_node)


@mark.order(2)
@mark.initial_setup
async def test_set_base64name(sth: STH, sensor_node_mac_address, json_metadata):
    """Set Sensor Node Name to Base64-encoded MAC address
    
    This test:
    1. Reads the MAC address of the Sensor Node
    2. Converts it to Base64
    3. Renames the node to this name
    4. Stores the name in the JSON metadata
    
    IMPORTANT: Must be executed AFTER test_firmware_upload (order=2)
    """

    logger = getLogger(__name__)
    
    # Convert MAC address to Base64
    name = convert_mac_base64(sensor_node_mac_address)
    logger.info("Base64-encoded MAC address: %s", name)
    
    # Rename node
    await sth.eeprom.write_name(name)
    logger.info("Sensor Node renamed to: %s", name)
    
    # Store name in JSON metadata (for --json-report)
    json_metadata["Sensor Node Name"] = name
    logger.info("Name stored in JSON metadata")
    
    # Verify that the name was set correctly
    read_name = await sth.eeprom.read_name()
    assert read_name == name, (
        f"Read name '{read_name}' does not match set name '{name}'"
    )
