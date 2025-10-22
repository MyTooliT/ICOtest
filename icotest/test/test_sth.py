"""STH specific test code

Use this test code in addition to the one for the sensor node:

    icotest run -k 'sensor_node or sth'

"""

# -- Imports ------------------------------------------------------------------

from icotronic.can import STH
from icotronic.measurement.constants import ADC_MAX_VALUE

from icotest.config import settings
from icotest.test.node import check_write_read_eeprom_close
from icotest.test.sth import read_self_test_voltages

# -- Functions ----------------------------------------------------------------


async def test_acceleration_sensor_self_test(sth: STH):
    """Use the self test of a acceleration sensor to check for problems

    Args:

        sth:

            The STH that contains the acceleration sensor

    """

    voltage_diff_abs, voltage_diff_before_after = (
        await read_self_test_voltages(sth)
    )

    sensor = settings.acceleration_sensor()

    voltage_diff_expected = sensor.self_test.voltage.difference
    voltage_diff_tolerance = sensor.self_test.voltage.tolerance

    voltage_diff_minimum = voltage_diff_expected - voltage_diff_tolerance
    voltage_diff_maximum = voltage_diff_expected + voltage_diff_tolerance

    assert voltage_diff_before_after <= voltage_diff_tolerance, (
        "Measured voltage difference between voltage before and after "
        f"test {voltage_diff_before_after:.2f} mV is larger than "
        f"tolerance of {voltage_diff_tolerance:.2f} mV"
    )
    possible_failure_reason = (
        "\n\nPossible Reason:\n\n• Acceleration sensor config value "
        f"“{settings.sth.acceleration_sensor.sensor}” is incorrect"
    )

    assert voltage_diff_minimum <= voltage_diff_abs, (
        f"Measured voltage difference of {voltage_diff_abs:.2f} mV is "
        "lower than expected minimum voltage difference of "
        f"{voltage_diff_minimum:.2f} mV{possible_failure_reason}"
    )
    assert voltage_diff_abs <= voltage_diff_maximum, (
        f"Measured voltage difference of {voltage_diff_abs:.2f} mV is "
        "greater than expected minimum voltage difference of "
        f"{voltage_diff_maximum:.2f} mV{possible_failure_reason}"
    )


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
