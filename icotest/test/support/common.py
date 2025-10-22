"""Common test support code"""

# -- Imports ------------------------------------------------------------------

from dynaconf.utils.boxing import DynaBox

# -- Functions ----------------------------------------------------------------


async def check_power_usage(power_usage: float, settings: DynaBox):
    """Test if the average power usage matches a certain value

    Args:

        power_usage:

            The measured power usage in mW

        settings:

            The settings object that contains the expected power usage values

    """

    average_power = settings.average
    tolerance = settings.tolerance

    minimum_power = average_power - tolerance
    maximum_power = average_power + tolerance
    assert minimum_power <= power_usage, (
        f"Power usage of {power_usage} mW smaller than expected minimum of "
        f"{minimum_power} mW"
    )
    assert power_usage <= maximum_power, (
        f"Power usage of {power_usage} mW larger than expected maximum of "
        f"{maximum_power} mW"
    )
