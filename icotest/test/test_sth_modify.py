"""Test sensor node hardware (SHA, STH, SMH…)

This code is used to make all the permanent changes to the hardware
to have it ready for production.
(e.g. uploading the firmware, change name after completion)

"""



# -- Imports ------------------------------------------------------------------

from asyncio import Event, TaskGroup, to_thread
from logging import getLogger

from icotronic.can import SensorNode, StreamingConfiguration, STU

from icotest.cli.commander import Commander
from icotest.config import settings
from icotest.test.support.common import check_power_usage
from icotest.test.support.mac import convert_mac_base64
from icotest.test.support.node import (
    check_connection,
    check_firmware_upload,
    check_eeprom_product_data,
    check_eeprom_statistics,
    check_eeprom_status,
)
from icotest.test.support.sensor_node import (
    check_eeprom_name,
    check_eeprom_bluetooth_times,
)

from icotronic.measurement.constants import ADC_MAX_VALUE

# -- Functions ----------------------------------------------------------------

async def test_firmware_upload():
    """Upload firmware"""

    await check_firmware_upload(settings.sensor_node)



async def test_set_base64name(sensor_node: SensorNode, capsys, json_metadata):
    """Set name to Base64 encoded MAC address of sensor node"""

    mac_address = await sensor_node.get_mac_address()
    getLogger().info("MAC address: %s", mac_address)
    name = convert_mac_base64(mac_address)
    with capsys.disabled():
        print(f"Base64 encoded MAC address (Bluetooth name): {name}")
    json_metadata["Sensor Node Name"] = name

    await sensor_node.set_name(name)

async def test_norbert_test(sensor_node: SensorNode, json_metadata):
    name = await sensor_node.get_name()
    getLogger(__name__).info("Node heißt: %s", name)
    json_metadata["Sensor Node Name"] = name"""STH Initial Setup Tests - Firmware Upload und Umbenennung

Diese Tests müssen in einer bestimmten Reihenfolge ausgeführt werden:
1. Firmware Upload (order=1)
2. Base64 Name setzen (order=2)
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
    """Upload firmware - MUSS als ERSTES ausgeführt werden"""

    await check_firmware_upload(settings.sensor_node)


@mark.order(2)
@mark.initial_setup
async def test_set_base64name(sth: STH, sensor_node_mac_address, json_metadata):
    """Setze Sensor Node Name auf Base64-kodierte MAC-Adresse
    
    Dieser Test:
    1. Liest die MAC-Adresse des Sensor Nodes
    2. Konvertiert sie zu Base64
    3. Benennt den Node auf diesen Namen um
    4. Speichert den Namen in den JSON-Metadaten
    
    WICHTIG: Muss NACH test_firmware_upload ausgeführt werden (order=2)
    """

    logger = getLogger(__name__)
    
    # MAC-Adresse zu Base64 konvertieren
    name = convert_mac_base64(sensor_node_mac_address)
    logger.info("Base64-kodierte MAC-Adresse: %s", name)
    
    # Node umbenennen
    await sth.eeprom.write_name(name)
    logger.info("Sensor Node umbenannt auf: %s", name)
    
    # Name in JSON-Metadaten speichern (für --json-report)
    json_metadata["Sensor Node Name"] = name
    logger.info("Name in JSON-Metadaten gespeichert")
    
    # Verifizieren dass der Name korrekt gesetzt wurde
    read_name = await sth.eeprom.read_name()
    assert read_name == name, (
        f"Gelesener Name '{read_name}' stimmt nicht mit gesetztem Namen '{name}' überein"
    )
