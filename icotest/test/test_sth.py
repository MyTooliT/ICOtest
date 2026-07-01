"""STH specific test code

Use this test code in addition to the one for the sensor node:

    icotest run -k 'sensor_node or sth'

"""

# -- Imports ------------------------------------------------------------------

from logging import getLogger
from math import ceil

from pytest import mark

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

# Order 30-39: Sensor Tests (Standard)


@mark.order(30)
@mark.sensor
async def test_acceleration_sensor_self_test(sth: STH, json_metadata: dict):
    """Use the self test of a acceleration sensor to check for problems"""

    logger = getLogger(__name__)
    logger.info("Starting acceleration sensor self-test")

    voltage_diff_abs, voltage_diff_before_after = (
        await read_self_test_voltages(sth)
    )

    logger.info("Voltage difference (absolute): %.2f mV", voltage_diff_abs)
    logger.info(
        "Voltage difference (before/after): %.2f mV", voltage_diff_before_after
    )

    sensor = settings.acceleration_sensor()

    voltage_diff_expected = sensor.self_test.voltage.difference
    voltage_diff_tolerance = sensor.self_test.voltage.tolerance

    voltage_diff_minimum = voltage_diff_expected - voltage_diff_tolerance
    voltage_diff_maximum = voltage_diff_expected + voltage_diff_tolerance

    logger.info(
        "Expected voltage difference: %.2f mV (±%.2f mV)",
        voltage_diff_expected,
        voltage_diff_tolerance,
    )
    logger.info(
        "Acceptable range: %.2f mV to %.2f mV",
        voltage_diff_minimum,
        voltage_diff_maximum,
    )

    # Store in JSON report
    json_metadata["record"](
        "self_test_voltage_abs",
        voltage_diff_abs,
        unit="mV",
        lower=voltage_diff_minimum,
        upper=voltage_diff_maximum,
        description="Absolute voltage difference during self-test",
    )
    json_metadata["record"](
        "self_test_voltage_drift",
        voltage_diff_before_after,
        unit="mV",
        upper=voltage_diff_tolerance,
        description="Drift between voltage before and after self-test",
    )

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


@mark.order(31)
@mark.sensor
async def test_acceleration_single_value(sth: STH):
    """Test stationary acceleration value"""

    logger = getLogger(__name__)
    logger.info("Starting single acceleration value test")

    stream_data = await sth.get_streaming_data_single()
    sensor = settings.acceleration_sensor()
    acceleration = convert_raw_to_g(
        stream_data.values[0], sensor.acceleration.maximum
    )

    logger.info("Raw value: %d", stream_data.values[0])
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


@mark.order(32)
@mark.sensor
async def test_acceleration_noise(sth: STH, json_metadata: dict):
    """Test ratio of noise to maximal possible measurement value"""

    logger = getLogger(__name__)
    logger.info("Starting acceleration noise test")

    number_values = 10_000
    logger.info(
        "Collecting %d values (%d streaming messages)",
        number_values,
        ceil(number_values / 3),
    )

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

    mean_value_raw = sum(acceleration) / len(acceleration)
    mean_value = convert_raw_to_g(mean_value_raw, 100.0)
    logger.info(
        "SNR: %.2f dB (max allowed: %.2f dB)",
        ratio_noise_maximum,
        maximum_ratio_allowed,
    )
    logger.info("Mean acceleration: %.2f g", mean_value)

    # Store in JSON report
    json_metadata["record"](
        "acceleration_noise_snr",
        ratio_noise_maximum,
        unit="dB",
        upper=maximum_ratio_allowed,
        description="Signal-to-Noise Ratio for acceleration",
    )
    json_metadata["record"](
        "acceleration_mean",
        mean_value,
        unit="g",
        description="Mean acceleration measured during noise test",
    )
    # Store FULL recording
    json_metadata["acceleration_full_recording"] = [
        int(v) for v in acceleration
    ]

    assert ratio_noise_maximum <= maximum_ratio_allowed, (
        "The ratio noise to possible maximum measured value of "
        f"{ratio_noise_maximum} dB is higher than the maximum allowed level "
        f"of {maximum_ratio_allowed} dB"
    )

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

    mean_value = convert_raw_to_g(
        (sum(acceleration) / len(acceleration)), 100.0
    )
    logger.info(
        "SNR: %.2f dB (max allowed: %.2f dB)",
        ratio_noise_maximum,
        maximum_ratio_allowed,
    )
    logger.info("Mean acceleration: %.2f g", mean_value)

    assert ratio_noise_maximum <= maximum_ratio_allowed, (
        "The ratio noise to possible maximum measured value of "
        f"{ratio_noise_maximum} dB is higher than the maximum allowed level "
        f"of {maximum_ratio_allowed} dB"
    )


# pylint: disable=too-many-locals


@mark.order(33)
@mark.sensor
async def test_acceleration_3a_alt(sth: STH):
    """Test the triple axis accelerometer reading"""

    logger = getLogger(__name__)
    logger.info("Starting triple axis acceleration test (alternative method)")

    # Configure all of these using the config file
    # Assume it lies on the table
    # test_acc_tollerance_g = 0.5

    test_acc_tollerance_g = 2.5
    # test_acc_tollerance = np.array([0.5, 0.5, 0.5])
    test_acc_noise = np.array([50.0, 50.0, 50.0])

    logger.info(
        "Tolerance: %.2f g, Noise limits: %.2f/%.2f/%.2f dB",
        test_acc_tollerance_g,
        test_acc_noise[0],
        test_acc_noise[1],
        test_acc_noise[2],
    )

    logger.info(
        "Configuring ADC: prescaler=2, acq_time=8, oversampling=64,"
        " ref_voltage=1.8V"
    )
    await sth.set_adc_configuration(
        prescaler=2,
        acquisition_time=8,
        oversampling_rate=64,
        reference_voltage=1.8,
    )

    logger.info("Setting sensor channels: first=2, second=3, third=4")
    # Set the correct channels
    await sth.set_sensor_configuration(
        SensorConfiguration(first=2, second=3, third=4)
    )

    acc_bias = []
    acc_noise = []
    # How long should the recording sample be
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

        # This block strips the metadata since we seem to always be getting a
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

        # Put it into the list for analysis
        acc_bias.append(acceleration_g)
        acc_noise.append(acceleration_noise)

    # Store the results into the json file
    # json_metadata["Sensor Node Name"] = name

    # Subtract the expected gravity
    earth_acc = 1.0
    acc_bias_error = np.linalg.norm(np.array(acc_bias)) - earth_acc
    logger.info(
        "Measured acceleration vector: [%.2f, %.2f, %.2f] g",
        acc_bias[0],
        acc_bias[1],
        acc_bias[2],
    )
    logger.info(
        "Bias check - expected: %.2f g, error: %.2f g",
        earth_acc,
        acc_bias_error,
    )
    assert acc_bias_error < test_acc_tollerance_g, (
        f"Accelerometer offset error {acc_bias_error:.3f} g is higher than "
        f"{test_acc_tollerance_g:.3f} g "
        f"the measured values are {acc_bias[0]:.3f} {acc_bias[1]:.3f} "
        f"{acc_bias[2]:.3f} g"
    )

    acc_noise_margin = np.max(acc_noise + test_acc_noise)
    logger.info(
        "Measured noise: [%.2f, %.2f, %.2f] dB",
        acc_noise[0],
        acc_noise[1],
        acc_noise[2],
    )
    logger.info(
        "Noise check - expected threshold: %.2f dB, worst channel margin:"
        " %.2f dB",
        np.mean(test_acc_noise),
        acc_noise_margin,
    )
    assert acc_noise_margin < 0.0, (
        "Accelerometer noise error! The noise margin is "
        f"{acc_noise_margin:.3f} "
        f"the measured values are {acc_noise[0]:.3f} {acc_noise[1]:.3f} "
        f"{acc_noise[2]:.3f} dB"
    )


# pylint: disable=too-many-statements


@mark.order(34)
@mark.sensor
async def test_acceleration_3a_optimized(sth: STH, json_metadata: dict):
    """Test the triple axis accelerometer reading (optimized version)"""

    logger = getLogger(__name__)
    logger.info("Starting triple axis acceleration test (optimized method)")

    # pylint: disable=fixme
    # TODO: configure all of these using the config file
    # pylint: enable=fixme
    # We use the vector representation of the acceleration therefore
    # placement of the board should make no difference.
    test_acc_tollerance_g = 2.5
    test_acc_noise = np.array([50.0, 50.0, 50.0])

    logger.info(
        "Tolerance: %.2f g, Noise limits: %.2f/%.2f/%.2f dB",
        test_acc_tollerance_g,
        test_acc_noise[0],
        test_acc_noise[1],
        test_acc_noise[2],
    )

    logger.info(
        "Configuring ADC: prescaler=2, acq_time=8, oversampling=64,"
        " ref_voltage=1.8V"
    )
    await sth.set_adc_configuration(
        prescaler=2,
        acquisition_time=8,
        oversampling_rate=64,
        reference_voltage=1.8,
    )

    logger.info("Setting sensor channels: first=2, second=3, third=4")
    # set the correct channels
    await sth.set_sensor_configuration(
        SensorConfiguration(first=2, second=3, third=4)
    )

    # How long should the recording sample be
    number_values = 10_000
    logger.info(
        "Collecting %d values from all three channels simultaneously",
        number_values,
    )

    # We want `number_values` values which means we need to collect data from
    # `number_values/3` messages, if we use a single channel
    number_streaming_messages = ceil(number_values / 3)

    # Stream all three channels simultaneously
    config = StreamingConfiguration(first=True, second=True, third=True)
    logger.info("Streaming config: %s", config)
    measurement_data = await read_streaming_data(
        sth, config, length=number_streaming_messages
    )

    # Extract raw data from each channel
    acceleration_x_raw = np.array(measurement_data.first().values())
    acceleration_y_raw = np.array(measurement_data.second().values())
    acceleration_z_raw = np.array(measurement_data.third().values())

    # Convert to g and calculate noise for each axis
    acc_bias = []
    acc_noise = []

    # Store FULL recordings in metadata
    json_metadata["acceleration_x_recording"] = [
        int(v) for v in acceleration_x_raw
    ]
    json_metadata["acceleration_y_recording"] = [
        int(v) for v in acceleration_y_raw
    ]
    json_metadata["acceleration_z_recording"] = [
        int(v) for v in acceleration_z_raw
    ]

    for axis_name, acceleration_raw in [
        ("x", acceleration_x_raw),
        ("y", acceleration_y_raw),
        ("z", acceleration_z_raw),
    ]:
        acceleration_g = (mean(acceleration_raw) + 400 - exp2(15)) * 1.3733e-3
        acceleration_noise = ratio_noise_max(acceleration_raw)

        getLogger(__name__).info(
            'Channel "%s": mean raw value = %.2f, acceleration = %.2f g, SNR ='
            " %.2f dB",
            axis_name,
            mean(acceleration_raw),
            acceleration_g,
            acceleration_noise,
        )

        acc_bias.append(acceleration_g)
        acc_noise.append(acceleration_noise)

        # Record per-axis results
        json_metadata["record"](
            f"acceleration_{axis_name}_bias", acceleration_g, unit="g"
        )
        json_metadata["record"](
            f"acceleration_{axis_name}_snr", acceleration_noise, unit="dB"
        )

    # subtract the expected gravity
    earth_acc = 1.0
    acc_bias_vector = np.array(acc_bias)
    acc_bias_error = np.linalg.norm(acc_bias_vector) - earth_acc

    logger.info(
        "Measured acceleration vector: [%.2f, %.2f, %.2f] g",
        acc_bias[0],
        acc_bias[1],
        acc_bias[2],
    )
    logger.info(
        "Bias check - expected: %.2f g, measured error: %.2f g",
        earth_acc,
        acc_bias_error,
    )

    # Store vector results
    json_metadata["record"](
        "acceleration_vector_error",
        acc_bias_error,
        unit="g",
        upper=test_acc_tollerance_g,
        description="Total acceleration vector error magnitude compared to 1g",
    )

    assert acc_bias_error < test_acc_tollerance_g, (
        f"Accelerometer offset error {acc_bias_error:.3f} g is higher than "
        f"{test_acc_tollerance_g:.3f} g "
        f"the measured values are {acc_bias[0]:.3f} {acc_bias[1]:.3f} "
        f"{acc_bias[2]:.3f} g"
    )

    acc_noise_margin = np.max(acc_noise + test_acc_noise)
    logger.info(
        "Measured noise: [%.2f, %.2f, %.2f] dB",
        acc_noise[0],
        acc_noise[1],
        acc_noise[2],
    )
    logger.info(
        "Noise check - expected threshold: %.2f dB, worst channel margin:"
        " %.2f dB",
        np.mean(test_acc_noise),
        acc_noise_margin,
    )

    json_metadata["record"](
        "acceleration_noise_margin",
        acc_noise_margin,
        upper=0.0,
        description=(
            "Worst-case margin against noise limits across all channels"
        ),
    )

    assert acc_noise_margin < 0.0, (
        "Accelerometer noise error! The noise margin is "
        f"{acc_noise_margin:.3f} "
        f"the measured values are {acc_noise[0]:.3f} {acc_noise[1]:.3f} "
        f"{acc_noise[2]:.3f} dB"
    )

    logger.info(
        "Configuring ADC: prescaler=2, acq_time=8, oversampling=64,"
        " ref_voltage=1.8V"
    )
    await sth.set_adc_configuration(
        prescaler=2,
        acquisition_time=8,
        oversampling_rate=64,
        reference_voltage=1.8,
    )

    logger.info("Setting sensor channels: first=2, second=3, third=4")
    # set the correct channels
    await sth.set_sensor_configuration(
        SensorConfiguration(first=2, second=3, third=4)
    )

    # How long should the recording sample be
    number_values = 10_000
    logger.info(
        "Collecting %d values from all three channels simultaneously",
        number_values,
    )

    # We want `number_values` values which means we need to collect data from
    # `number_values/3` messages, if we use a single channel
    number_streaming_messages = ceil(number_values / 3)

    # Stream all three channels simultaneously
    config = StreamingConfiguration(first=True, second=True, third=True)
    logger.info("Streaming config: %s", config)
    measurement_data = await read_streaming_data(
        sth, config, length=number_streaming_messages
    )

    # Extract raw data from each channel
    acceleration_x_raw = np.array(measurement_data.first().values())
    acceleration_y_raw = np.array(measurement_data.second().values())
    acceleration_z_raw = np.array(measurement_data.third().values())

    # Convert to g and calculate noise for each axis
    acc_bias = []
    acc_noise = []

    for axis_name, acceleration_raw in [
        ("x", acceleration_x_raw),
        ("y", acceleration_y_raw),
        ("z", acceleration_z_raw),
    ]:
        acceleration_g = (mean(acceleration_raw) + 400 - exp2(15)) * 1.3733e-3
        acceleration_noise = ratio_noise_max(acceleration_raw)

        getLogger(__name__).info(
            'Channel "%s": mean raw value = %.2f, acceleration = %.2f g, SNR ='
            " %.2f dB",
            axis_name,
            mean(acceleration_raw),
            acceleration_g,
            acceleration_noise,
        )

        acc_bias.append(acceleration_g)
        acc_noise.append(acceleration_noise)

    # subtract the expected gravity
    earth_acc = 1.0
    acc_bias_error = np.linalg.norm(np.array(acc_bias)) - earth_acc
    logger.info(
        "Measured acceleration vector: [%.2f, %.2f, %.2f] g",
        acc_bias[0],
        acc_bias[1],
        acc_bias[2],
    )
    logger.info(
        "Bias check - expected: %.2f g, measured error: %.2f g",
        earth_acc,
        acc_bias_error,
    )
    assert acc_bias_error < test_acc_tollerance_g, (
        f"Accelerometer offset error {acc_bias_error:.3f} g is higher than "
        f"{test_acc_tollerance_g:.3f} g "
        f"the measured values are {acc_bias[0]:.3f} {acc_bias[1]:.3f} "
        f"{acc_bias[2]:.3f} g"
    )

    acc_noise_margin = np.max(acc_noise + test_acc_noise)
    logger.info(
        "Measured noise: [%.2f, %.2f, %.2f] dB",
        acc_noise[0],
        acc_noise[1],
        acc_noise[2],
    )
    logger.info(
        "Noise check - expected threshold: %.2f dB, worst channel margin:"
        " %.2f dB",
        np.mean(test_acc_noise),
        acc_noise_margin,
    )
    assert acc_noise_margin < 0.0, (
        "Accelerometer noise error! The noise margin is "
        f"{acc_noise_margin:.3f} "
        f"the measured values are {acc_noise[0]:.3f} {acc_noise[1]:.3f} "
        f"{acc_noise[2]:.3f} dB"
    )


# pylint: enable=too-many-locals, too-many-statements

# Order 40-49: BackPack Tests


# pylint: disable=invalid-name, too-many-locals, too-many-statements


@mark.order(40)
@mark.backpack
async def test_BaP_torr_accelleration(sth: STH, json_metadata: dict):
    """Test the triple axis accelerometer reading"""

    logger = getLogger(__name__)
    logger.info("Starting BackPack torr acceleration test")

    test_acc_tollerance_g = 2.5
    test_noise_limit_db = -85

    logger.info(
        "Tolerance: %.2f g, Noise limit: %.2f dB",
        test_acc_tollerance_g,
        test_noise_limit_db,
    )
    logger.info("Setting BackPack sensor channels: first=7, second=8, third=9")

    # Set the correct channels to address BackPack
    await sth.set_sensor_configuration(
        SensorConfiguration(first=7, second=8, third=9)
    )

    # How long should the recording sample be
    number_values = 10_000
    logger.info("Collecting %d values from all three channels", number_values)

    # We want `number_values` values which means we need to collect data from
    # `number_values/3` messages, if we use a single channel
    number_streaming_messages = ceil(number_values / 3)

    # setup the stream to collect the samples from all the three channels
    config = StreamingConfiguration(first=True, second=True, third=True)
    logger.info("Streaming config: %s", config)
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

    # This block strips the metadata since we seem to always be getting a
    # 3xN array
    acceleration_x = (acceleration_x_raw / 65535 - 0.5) * 200
    # The combination sensors add up which results in an inherent gain of two
    acceleration_y = (acceleration_y_raw / 65535 - 0.5) * 100
    acceleration_torr = (acceleration_torr_raw / 65535 - 0.5) * 100

    # Store FULL recordings
    json_metadata["backpack_x_recording"] = [
        int(v) for v in acceleration_x_raw
    ]
    json_metadata["backpack_y_recording"] = [
        int(v) for v in acceleration_y_raw
    ]
    json_metadata["backpack_torr_recording"] = [
        int(v) for v in acceleration_torr_raw
    ]

    acc_bias_x = mean(acceleration_x)
    acc_bias_y = mean(acceleration_y)
    acc_bias_torr = mean(acceleration_torr)

    acceleration_noise_x = ratio_noise_max(acceleration_x)
    acceleration_noise_y = ratio_noise_max(acceleration_y)
    acceleration_noise_torr = ratio_noise_max(acceleration_torr)

    logger.info(
        "Channel X - mean: %.2f g, SNR: %.2f dB",
        acc_bias_x,
        acceleration_noise_x,
    )
    logger.info(
        "Channel Y - mean: %.2f g, SNR: %.2f dB",
        acc_bias_y,
        acceleration_noise_y,
    )
    logger.info(
        "Channel torr - mean: %.2f g, SNR: %.2f dB",
        acc_bias_torr,
        acceleration_noise_torr,
    )

    # Store in JSON report
    json_metadata["record"]("backpack_acc_x_bias", acc_bias_x, unit="g")
    json_metadata["record"]("backpack_acc_y_bias", acc_bias_y, unit="g")
    json_metadata["record"]("backpack_acc_torr_bias", acc_bias_torr, unit="g")

    json_metadata["record"](
        "backpack_acc_x_snr", acceleration_noise_x, unit="dB"
    )
    json_metadata["record"](
        "backpack_acc_y_snr", acceleration_noise_y, unit="dB"
    )
    json_metadata["record"](
        "backpack_acc_torr_snr", acceleration_noise_torr, unit="dB"
    )

    max_bias = max(acc_bias_x, acc_bias_y, acc_bias_torr)
    max_noise = max(
        acceleration_noise_x, acceleration_noise_y, acceleration_noise_torr
    )

    json_metadata["record"](
        "backpack_max_bias", max_bias, unit="g", upper=test_acc_tollerance_g
    )
    json_metadata["record"](
        "backpack_max_noise", max_noise, unit="dB", upper=test_noise_limit_db
    )

    assert max_bias < test_acc_tollerance_g, (
        "Accelerometer offset error! Over the limit of"
        f" {test_acc_tollerance_g} gthe measured values are X:"
        f" {acc_bias_x:.3f} Y: {acc_bias_y:.3f} torr: {acc_bias_torr:.3f} g >"
        f" {test_acc_tollerance_g:.3f} "
    )

    assert max_noise < test_noise_limit_db, (
        "Accelerometer noise error! Over the limit of"
        f" {test_noise_limit_db:.3f} dB the measured values are x:"
        f" {acceleration_noise_x:.3f} y: {acceleration_noise_y:.3f} torr:"
        f" {acceleration_noise_torr:.3f} dB"
    )

    logger.info("Setting BackPack sensor channels: first=7, second=8, third=9")

    # Set the correct channels to address BackPack
    await sth.set_sensor_configuration(
        SensorConfiguration(first=7, second=8, third=9)
    )

    # How long should the recording sample be
    number_values = 10_000
    logger.info("Collecting %d values from all three channels", number_values)

    # We want `number_values` values which means we need to collect data from
    # `number_values/3` messages, if we use a single channel
    number_streaming_messages = ceil(number_values / 3)

    # setup the stream to collect the samples from all the three channels
    config = StreamingConfiguration(first=True, second=True, third=True)
    logger.info("Streaming config: %s", config)
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

    # This block strips the metadata since we seem to always be getting a
    # 3xN array
    acceleration_x = (acceleration_x_raw / 65535 - 0.5) * 200
    # The combination sensors add up which results in an inherent gain of two
    acceleration_y = (acceleration_y_raw / 65535 - 0.5) * 100
    acceleration_torr = (acceleration_torr_raw / 65535 - 0.5) * 100

    acc_bias_x = mean(acceleration_x)
    acc_bias_y = mean(acceleration_y)
    acc_bias_torr = mean(acceleration_torr)

    acceleration_noise_x = ratio_noise_max(acceleration_x)
    acceleration_noise_y = ratio_noise_max(acceleration_y)
    acceleration_noise_torr = ratio_noise_max(acceleration_torr)

    logger.info(
        "Channel X - mean: %.2f g, SNR: %.2f dB",
        acc_bias_x,
        acceleration_noise_x,
    )
    logger.info(
        "Channel Y - mean: %.2f g, SNR: %.2f dB",
        acc_bias_y,
        acceleration_noise_y,
    )
    logger.info(
        "Channel torr - mean: %.2f g, SNR: %.2f dB",
        acc_bias_torr,
        acceleration_noise_torr,
    )

    # Store the results into the json file
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


# pylint: enable=invalid-name, too-many-locals, too-many-statements

# Order 10-19: Basic Tests


@mark.order(13)
@mark.basic
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
