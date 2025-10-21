"""STH specific test code

Use this test code in addition to the one for the sensor node:

    icotest run -k 'sensor_node or sth'

"""

# -- Imports ------------------------------------------------------------------

from icotronic.can import STH
from icotronic.measurement.constants import ADC_MAX_VALUE

from icotest.config import settings
from icotest.test.node import check_write_read_eeprom_close

# -- Functions ----------------------------------------------------------------


async def test_eeprom(sth: STH):
    """Test if reading and writing STH EEPROM data works

    Args:

        sth:

            The STH that should be checked

    """

    sensor = settings.acceleration_sensor()
    acceleration_max = sensor.acceleration.maximum

    acceleration_slope = acceleration_max / ADC_MAX_VALUE
    acceleration_offset = -(acceleration_max / 2)

    for axis in ("x", "y", "z"):
        await check_write_read_eeprom_close(
            sth, f"{axis} axis acceleration slope", acceleration_slope
        )
        await check_write_read_eeprom_close(
            sth, f"{axis} axis acceleration offset", acceleration_offset
        )
