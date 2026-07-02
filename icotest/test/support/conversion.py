"""Conversion functions"""

from icotronic.measurement.constants import ADC_MAX_VALUE

# -- Functions ----------------------------------------------------------------


def convert_raw_to_g(acceleration_raw: float, max_value: float) -> float:
    """Convert an acceleration value sent by the STH into a factor

    The factor measures the amount of the gravitational force
    (g₀ = 9.807 m/s²) applied to the STH.

    Args:

        acceleration_raw:
            The 16 bit integer acceleration value as sent by the STH

        max_value:
            The maximum acceleration value as factor of g₀
            (e.g. 200 for a ±100 g sensor)

    Returns:

        The acceleration in multiples of the standard gravity g₀

    Examples:

        Convert a raw value (that represents ca. 0 g₀) into multiples of g₀

        >>> acceleration = convert_raw_to_g(2**15, max_value=200)
        >>> -0.01 < acceleration < 0.01
        True

    """

    acceleration_to_gravity = max_value

    # The code subtracts 1/2 from the computed value, since the STH linearly
    # maps the maximum negative acceleration to 0 and the maximum positive
    # acceleration to the maximum ADC value.
    acceleration_in_g = (
        acceleration_raw / ADC_MAX_VALUE - 1 / 2
    ) * acceleration_to_gravity
    return acceleration_in_g
