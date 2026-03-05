"""STH Initial Setup Tests - Firmware Upload und Umbenennung

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
