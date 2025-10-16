"""Shared code for all nodes of the ICOtronic system (STU & sensor nodes)"""

# -- Imports ------------------------------------------------------------------

from dynaconf.utils.boxing import DynaBox
from icotronic.can import SensorNode, STU

# -- Functions ----------------------------------------------------------------


async def check_eeprom_gtin(node: SensorNode | STU, settings: DynaBox):
    """Test if reading and writing the GTIN works"""

    gtin_written = settings.gtin
    await node.eeprom.write_gtin(gtin_written)
    gtin_read = await node.eeprom.read_gtin()
    assert (
        gtin_written == gtin_read
    ), f"Written GTIN “{gtin_written}” does not match read GTIN “{gtin_read}”"
