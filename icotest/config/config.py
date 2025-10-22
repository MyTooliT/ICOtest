"""Support for changing configuration values for the tests"""

# -- Import -------------------------------------------------------------------

from datetime import date
from functools import partial
from importlib.resources import as_file, files
from numbers import Real
from pathlib import Path
from sys import exit as sys_exit, stderr


from dynaconf import (  # type: ignore[attr-defined]
    Dynaconf,
    ValidationError,
    Validator,
)

from dynaconf.vendor.ruamel.yaml.parser import ParserError
from dynaconf.vendor.ruamel.yaml.scanner import ScannerError

from startfile import startfile
from platformdirs import site_config_dir, user_config_dir

# -- Functions ----------------------------------------------------------------


def must_exist(*arguments, **keyword_arguments) -> Validator:
    """Return Validator which requires setting to exist

    Args:

        arguments:

            All positional arguments for the Validator

        keyword_arguments:

            All keyword arguments for the Validator

    """

    return Validator(*arguments, must_exist=True, **keyword_arguments)


def element_is_type(nodes, name: str, element_type: type):
    """Check that all elements of a list have a certain type

    Args:

        nodes:

            The parent node of the list that should be checked

        name:

            The name of the parent node

        element_type:

            The expected type of the nodes in the list

    Returns:

        ``True``, if every element has the expected type

    Raises:

        ``ValidationError``, if any element of the given list has the wrong
        type

    """

    if nodes is None:
        return True  # Let parent validator handle wrong type

    for node in nodes:
        if not isinstance(node, element_type):
            raise ValidationError(
                f"Element “{node}” of {name} has wrong type "
                f"“{type(node)}” instead of “{element_type}”"
            )
    return True


def element_is_int(nodes, name: str):
    """Check that all elements of a list are numbers

    Args:

        nodes:

            The parent node of the list that should be checked

        name:

            The name of the parent node

    Returns:

        ``True``, if every element has the type ``int``

    Raises:

        ``ValidationError``, if any element of the given list has a type other
        than ``int``

    """

    return element_is_type(nodes, name, element_type=int)


def element_is_string(nodes, name: str):
    """Check that all elements of a list are strings

    Args:

        nodes:

            The parent node of the list that should be checked

        name:

            The name of the parent node

    Returns:

        ``True``, if every element has the type ``str``

    Raises:

        ``ValidationError``, if any element of the given list has a type other
        than ``str``

    """

    return element_is_type(nodes, name, element_type=str)


def commands_validators() -> list[Validator]:
    """Return list of validators for config data below key `commands`"""

    return [
        must_exist(
            f"commands.path.{os}",
            is_type_of=list,
            condition=partial(element_is_string, name=f"commands.path.{os}"),
        )
        for os in ("linux", "mac", "windows")
    ]


def acceleration_sensor_validators(name: str):
    """Return the list of validators for a specific acceleration sensor

    Args:

        name:

            The name of the acceleration sensor

    """

    prefix = "sth.acceleration_sensor"
    return [
        must_exist(
            f"{prefix}.{name}.acceleration.maximum",
            f"{prefix}.{name}.acceleration.tolerance",
            f"{prefix}.{name}.reference_voltage",
            f"{prefix}.{name}.self_test.voltage.difference",
            f"{prefix}.{name}.self_test.voltage.tolerance",
            is_type_of=Real,
        ),
        must_exist(
            f"{prefix}.{name}.self_test.dimension",
            is_type_of=str,
            is_in=("x", "y", "z"),
        ),
    ]


def node_validators(node: str) -> list[Validator]:
    """Get validators for node (STU & sensor node) configuration

    Args:

        node:

            The namespace of the node configuration

    Returns:

        A list of validators for the given node

    """

    return [
        must_exist(f"{node}.gtin", f"{node}.batch_number", is_type_of=int),
        must_exist(
            f"{node}.hardware_version",
            f"{node}.firmware.chip",
            f"{node}.firmware.location",
            f"{node}.firmware.release_name",
            f"{node}.product_name",
            f"{node}.serial_number",
            is_type_of=str,
        ),
        must_exist(
            f"{node}.oem_data",
            is_type_of=list,
            condition=partial(element_is_int, name="{node}.oem_data"),
        ),
        must_exist(
            f"{node}.production_date",
            is_type_of=date,
        ),
    ]


def sensor_node_validators() -> list[Validator]:
    """Return list of validators for config data below key `sensor_node`"""

    return node_validators("sensor_node") + [
        must_exist(
            "sensor_node.name",
            is_type_of=str,
        ),
        must_exist(
            "sensor_node.supply.voltage.average",
            "sensor_node.supply.voltage.tolerance",
            "sensor_node.power.connected.average",
            "sensor_node.power.connected.tolerance",
            "sensor_node.power.streaming.average",
            "sensor_node.power.streaming.tolerance",
            is_type_of=Real,
        ),
        must_exist(
            "sensor_node.bluetooth.advertisement_time_1",
            "sensor_node.bluetooth.advertisement_time_2",
            "sensor_node.bluetooth.sleep_time_1",
            "sensor_node.bluetooth.sleep_time_2",
            is_type_of=int,
        ),
    ]


def stu_validators() -> list[Validator]:
    """Return list of validators for config data below key `stu`"""

    return node_validators("stu")


def sth_validators() -> list[Validator]:
    """Return list of validators for config data below key `sth`"""

    validators = []
    for sensor in ("ADXL1001", "ADXL1002", "ADXL356"):
        validators.extend(acceleration_sensor_validators(sensor))

    return validators


def handle_incorrect_settings(error_message: str) -> None:
    """Handle incorrect configuration

    Args:

        error_message:

            A text that describes the configuration error

    """

    print(error_message, file=stderr)
    print(
        "\n"
        "• Most likely this problem is caused by an incorrect user "
        "configuration.\n"
        "• Please fix the problem and try again afterwards.\n\n"
        "Opening your user config file in your text editor now",
        file=stderr,
    )
    ConfigurationUtility.open_user_config()
    sys_exit(1)


# -- Classes ------------------------------------------------------------------


class ConfigurationUtility:
    """Access configuration data"""

    app_name = "ICOtest"
    app_author = "MyTooliT"
    config_filename = "config.yaml"
    site_config_filepath = (
        Path(site_config_dir(app_name, appauthor=app_author)) / config_filename
    )
    user_config_filepath = (
        Path(user_config_dir(app_name, appauthor=app_author)) / config_filename
    )

    @staticmethod
    def open_config_file(filepath: Path):
        """Open configuration file

        Args:

            filepath:
                Path to configuration file

        """

        # Create file, if it does not exist already
        if not filepath.exists():
            filepath.parent.mkdir(
                exist_ok=True,
                parents=True,
            )

            default_user_config = (
                files("icotest.config")
                .joinpath("user.yaml")
                .read_text(encoding="utf-8")
            )

            with filepath.open("w", encoding="utf8") as config_file:
                config_file.write(default_user_config)

        startfile(filepath)

    @classmethod
    def open_user_config(cls):
        """Open the current users configuration file"""

        try:
            cls.open_config_file(cls.user_config_filepath)
        except FileNotFoundError as error:
            print(
                f"Unable to open user configuration: {error}"
                "\nTo work around this problem please open "
                f"“{cls.user_config_filepath}” in your favorite text "
                "editor",
                file=stderr,
            )


class SettingsIncorrectError(Exception):
    """Raised when the configuration is incorrect"""


class Settings(Dynaconf):
    """Small extension of the settings object for our purposes

    Args:

        default_settings_filepath:
            Filepath to default settings file

        setting_files:
            A list containing setting files in ascending order according to
            importance (most important last).

        arguments:
            All positional arguments

        keyword_arguments:
            All keyword arguments

    """

    def __init__(
        self,
        default_settings_filepath,
        *arguments,
        settings_files: list[str] | None = None,
        **keyword_arguments,
    ) -> None:

        if settings_files is None:
            settings_files = []

        settings_files = [
            default_settings_filepath,
            ConfigurationUtility.site_config_filepath,
            ConfigurationUtility.user_config_filepath,
        ] + settings_files

        super().__init__(
            settings_files=settings_files,
            *arguments,
            **keyword_arguments,
        )
        self.validate_settings()

    def validate_settings(self) -> None:
        """Check settings for errors"""

        self.validators.register(
            *commands_validators(),
            *sensor_node_validators(),
            *sth_validators(),
            *stu_validators(),
        )

        try:
            self.validators.validate()
        except ValidationError as error:
            raise SettingsIncorrectError(
                f"Incorrect configuration: {error}"
            ) from error

    def acceleration_sensor(self):
        """Get the settings for the current acceleration sensor

        Returns:

            A configuration object for the currently selected accelerometer
            sensor

        """

        sensor_settings = self.sth.acceleration_sensor
        return sensor_settings[sensor_settings.sensor]


# -- Attributes ---------------------------------------------------------------


with as_file(
    files("icotest.config").joinpath("config.yaml")
) as repo_settings_filepath:
    try:
        settings = Settings(default_settings_filepath=repo_settings_filepath)
    except SettingsIncorrectError as settings_incorrect_error:
        handle_incorrect_settings(f"{settings_incorrect_error}")
    except (ParserError, ScannerError) as parsing_error:
        handle_incorrect_settings(
            f"Unable to parse configuration: {parsing_error}"
        )
