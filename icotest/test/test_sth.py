"""STH specific test code

Use this test code in addition to the one for the sensor node:

    icotest run -k 'sensor_node or sth'

"""

# -- Imports ------------------------------------------------------------------

from logging import getLogger
from math import ceil

from icotronic.can import STH, StreamingConfiguration
from icotronic.measurement.constants import ADC_MAX_VALUE
from icotronic.measurement import convert_raw_to_g, ratio_noise_max

from icotest.config import settings
from icotest.test.support.node import check_write_read_eeprom_close
from icotest.test.support.sensor_node import read_streaming_data
from icotest.test.support.sth import read_self_test_voltages
from icotronic.can import SensorConfiguration

from statistics import mean
from math import exp2
import numpy as np

# -- Functions ----------------------------------------------------------------


async def test_acceleration_sensor_self_test(sth: STH):
    """Use the self test of a acceleration sensor to check for problems"""

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


async def test_acceleration_single_value(sth: STH):
    """Test stationary acceleration value"""

    stream_data = await sth.get_streaming_data_single()
    sensor = settings.acceleration_sensor()
    acceleration = convert_raw_to_g(
        stream_data.values[0], sensor.acceleration.maximum
    )

    logger = getLogger(__file__)
    logger.info("Measured acceleration value: %.2f g", acceleration)

    # We expect a stationary acceleration between -g₀ and g₀ (g₀ = 9.807 m/s²)
    expected_acceleration = 0
    tolerance_acceleration = sensor.acceleration.tolerance
    expected_minimum_acceleration = (
        expected_acceleration - tolerance_acceleration
    )
    expected_maximum_acceleration = (
        expected_acceleration + tolerance_acceleration
    )

    assert expected_minimum_acceleration <= acceleration, (
        f"Measured acceleration {acceleration:.3f} g is lower "
        "than expected minimum acceleration "
        f"{expected_minimum_acceleration:.3f} g"
    )
    assert acceleration <= expected_maximum_acceleration, (
        f"Measured acceleration {acceleration:.3f} g is greater "
        "than expected maximum acceleration "
        f"{expected_maximum_acceleration:.3f} g"
    )


async def test_acceleration_noise(sth: STH):
    """Test ratio of noise to maximal possible measurement value"""

    number_values = 10_000
    # We want `number_values` values which means we need to collect data from
    # `number_values/3` messages, if we use a single channel
    number_streaming_messages = ceil(number_values / 3)
    measurement_data = await read_streaming_data(
        sth,
        StreamingConfiguration(first=True),
        length=number_streaming_messages,
    )

    values = measurement_data.values()
    assert number_values <= len(values) <= number_values + 2
    acceleration = values[:number_values]
    assert len(acceleration) == number_values

    ratio_noise_maximum = ratio_noise_max(acceleration)
    sensor = settings.acceleration_sensor()
    maximum_ratio_allowed = sensor.acceleration.ratio_noise_to_max_value
    getLogger(__name__).info(
        "SNR: %f [dB]",
        ratio_noise_maximum,
    )

    assert ratio_noise_maximum <= maximum_ratio_allowed, (
        "The ratio noise to possible maximum measured value of "
        f"{ratio_noise_maximum} dB is higher than the maximum allowed level "
        f"of {maximum_ratio_allowed} dB"
    )

    mean = convert_raw_to_g((sum(acceleration) / len(acceleration)), 100.0)
    getLogger(__name__).info(
        "SNR: %s [dB] , mean: %.2f g", ratio_noise_maximum, mean
    )


async def test_acceleration_3a_alt(sth: STH):
    """Test the triple axis accelerometer reading"""

    # configure all of those using the config file
    # assume it lies on the table
    test_acc_bias = np.array([1.0, 0.0, 0.0])
    # test_acc_tollerance_g = 0.5

    test_acc_tollerance_g = 2.5
    # test_acc_tollerance = np.array([0.5, 0.5, 0.5])
    test_acc_noise = np.array([50.0, 50.0, 50.0])

    await sth.set_adc_configuration(
        prescaler=2,
        acquisition_time=8,
        oversampling_rate=64,
        reference_voltage=1.8,
    )

    # set the correct channels
    await sth.set_sensor_configuration(
        SensorConfiguration(first=2, second=3, third=4)
    )

    acc_bias = []
    acc_noise = []
    # how long should the recording sample be
    number_values = 10_000

    # We want `number_values` values which means we need to collect data from
    # `number_values/3` messages, if we use a single channel
    number_streaming_messages = ceil(number_values / 3)

    for channel in ("first", "second", "third"):
        if channel == "first":
            config = StreamingConfiguration(first=True)
        else:
            config = StreamingConfiguration(first=False, **{channel: True})
        getLogger(__name__).info("🎛️ Config: %s", config)
        measurement_data = await read_streaming_data(
            sth, config, length=number_streaming_messages
        )

        # this block strips the meta data since we seem to be always getting
        # 3xN array
        all_values = (
            measurement_data.first().data
            + measurement_data.second().data
            + measurement_data.third().data
        )
        acceleration = [datapoint.value for datapoint in all_values]

        acceleration_g = (mean(acceleration) + 400 - exp2(15)) * 1.3733e-3
        acceleration_noise = ratio_noise_max(acceleration)

        getLogger(__name__).info(
            "🫣 Channel “%s” mean: %.2f = %.2f g @ SNR: %.2f dB",
            channel,
            mean(acceleration),
            acceleration_g,
            acceleration_noise,
        )

        # put in into the list for analysis
        acc_bias.append(acceleration_g)
        acc_noise.append(acceleration_noise)

    # store the results into the json file
    # json_metadata["Sensor Node Name"] = name

    # subtract the expected gravity
    earth_acc = 1.0
    acc_bias_error = np.linalg.norm(np.array(acc_bias)) - earth_acc
    getLogger(__name__).info(
        "Bias check, we expect %.2f g are off by %.2f g",
        earth_acc,
        acc_bias_error,
    )
    assert acc_bias_error < test_acc_tollerance_g, (
        f"Accelerometer offset error {acc_bias_error:.3f} g is higher than"
        f" {test_acc_tollerance_g:.3f} g the measured values are"
        f" {acc_bias[0]:.3f} {acc_bias[1]:.3f} {acc_bias[2]:.3f} g"
    )

    acc_noise_margin = np.max(acc_noise + test_acc_noise)
    getLogger(__name__).info(
        "Noise check, we expect about %.2f dB are off by %.2f dB in the worst"
        " channel",
        np.mean(test_acc_noise),
        acc_noise_margin,
    )
    assert acc_noise_margin < 0.0, (
        "Accelerometer noise error! The noise margin is"
        f" {acc_noise_margin:.3f} the measured values are {acc_noise[0]:.3f}"
        f" {acc_noise[1]:.3f} {acc_noise[2]:.3f} dB"
    )


async def test_BaP_torr_accelleration(sth: STH):
    """Test the triple axis accelerometer reading"""

    test_acc_tollerance_g = 2.5
    test_noise_limit_db = -85

    # set the correct channels to address Backpack
    await sth.set_sensor_configuration(
        SensorConfiguration(first=7, second=8, third=9)
    )

    acc_bias = []
    acc_noise = []

    # how long should the recording sample be
    number_values = 10_000

    # We want `number_values` values which means we need to collect data from
    # `number_values/3` messages, if we use a single channel
    number_streaming_messages = ceil(number_values / 3)

    # setup the stream to collect the samples from all the three channels
    config = StreamingConfiguration(first=True, second=True, third=True)
    measurement_data = await read_streaming_data(
        sth, config, length=number_streaming_messages
    )

    acceleration_x_raw = np.array(
        [datapoint.value for datapoint in measurement_data.first()]
    )
    acceleration_torr_raw = np.array(
        [datapoint.value for datapoint in measurement_data.second()]
    )
    acceleration_y_raw = np.array(
        [datapoint.value for datapoint in measurement_data.third()]
    )

    # this block strips the meta data since we seem to be always getting 3xN
    # array
    acceleration_x = (acceleration_x_raw / 65535 - 0.5) * 200
    # the combination sensors add up which results in an inherent gain of two
    acceleration_y = (acceleration_y_raw / 65535 - 0.5) * 100
    acceleration_torr = (acceleration_torr_raw / 65535 - 0.5) * 100

    acc_bias_x = mean(acceleration_x)
    acc_bias_y = mean(acceleration_y)
    acc_bias_torr = mean(acceleration_torr)

    acceleration_noise_x = ratio_noise_max(acceleration_x)
    acceleration_noise_y = ratio_noise_max(acceleration_y)
    acceleration_noise_torr = ratio_noise_max(acceleration_torr)

    getLogger(__name__).info(
        "Channel X,Y mean: %.2f g, %.2f g @ SNR: %.2f, %.2f dB",
        acc_bias_x,
        acc_bias_y,
        acceleration_noise_x,
        acceleration_noise_y,
    )
    # add some information because g is not really suitable here
    getLogger(__name__).info(
        "Channel torr mean: %.2f g @ SNR: %.2f",
        acc_bias_torr,
        acceleration_noise_torr,
    )

    # store the results into the json file
    # json_metadata["Sensor Node Name"] = name

    assert (
        max(acc_bias_x, acc_bias_y, acc_bias_torr) < test_acc_tollerance_g
    ), (
        "Accelerometer offset error! Over the limit of"
        f" {test_acc_tollerance_g} gthe measured values are X:"
        f" {acc_bias_x:.3f} Y: {acc_bias_y:.3f} torr: {acc_bias_torr:.3f} g >"
        f" {test_acc_tollerance_g:.3f} "
    )

    assert (
        max(
            acceleration_noise_x, acceleration_noise_y, acceleration_noise_torr
        )
        < test_noise_limit_db
    ), (
        "Accelerometer noise error! Over the limit of"
        f" {test_noise_limit_db:.3f} dB the measured values are x:"
        f" {acceleration_noise_x:.3f} y: {acceleration_noise_y:.3f} torr:"
        f" {acceleration_noise_torr:.3f} dB"
    )


async def test_eeprom(sth: STH):
    """Test if reading and writing STH EEPROM data works"""

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
