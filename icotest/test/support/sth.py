"""Shared code for STU"""

# -- Imports ------------------------------------------------------------------

from logging import getLogger
from icotronic.can import STH

from icotest.config import settings

# -- Functions ----------------------------------------------------------------


async def read_self_test_voltages(sth: STH) -> tuple[float, float]:
    """Read acceleration voltages before, at and after self test

    Args:

        sth:

            The STH where the measurement should take place
    Returns:

        A tuple containing the **absolute** i.e. positive difference:

        - between the voltage before and at the self test and

        - the value of the voltage before and after the self test

        in Millivolt.

    """

    logger = getLogger(__file__)

    sensor = settings.acceleration_sensor()
    dimension = sensor.self_test.dimension
    reference_voltage = sensor.reference_voltage

    voltage_before_test = await sth.get_acceleration_voltage(
        dimension, reference_voltage
    )
    logger.info("Voltage before test: %s V", voltage_before_test)

    await sth.activate_acceleration_self_test(dimension)
    voltage_at_test = await sth.get_acceleration_voltage(
        dimension, reference_voltage
    )
    logger.info("Voltage at test: %s V", voltage_at_test)

    await sth.deactivate_acceleration_self_test(dimension)
    voltage_after_test = await sth.get_acceleration_voltage(
        dimension, reference_voltage
    )
    logger.info("Voltage after test: %s V", voltage_after_test)

    voltage_diff = voltage_at_test - voltage_before_test
    voltage_diff_abs = abs(voltage_diff)
    voltage_diff_before_after = abs(voltage_before_test - voltage_after_test)

    return (voltage_diff_abs * 1000, voltage_diff_before_after * 1000)
