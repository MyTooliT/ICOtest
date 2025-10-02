"""Support for changing configuration values for the tests"""

# -- Import -------------------------------------------------------------------

from importlib.resources import as_file, files
from numbers import Real
from sys import exit as sys_exit, stderr

from dynaconf import Dynaconf, ValidationError, Validator
from dynaconf.vendor.ruamel.yaml.parser import ParserError
from dynaconf.vendor.ruamel.yaml.scanner import ScannerError

# -- Classes ------------------------------------------------------------------


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
        ] + settings_files

        super().__init__(
            settings_files=settings_files,
            *arguments,
            **keyword_arguments,
        )
        self.validate_settings()

    def validate_settings(self) -> None:
        """Check settings for errors"""

        def must_exist(*arguments, **keyword_arguments):
            """Return Validator which requires setting to exist"""

            return Validator(*arguments, must_exist=True, **keyword_arguments)

        sensor_node_validators = [
            must_exist(
                "sensor_node.battery_voltage.average",
                "sensor_node.battery_voltage.tolerance",
                is_type_of=Real,
            ),
            must_exist(
                "sensor_node.name",
                is_type_of=str,
            ),
        ]

        self.validators.register(*sensor_node_validators)

        try:
            self.validators.validate()
        except ValidationError as error:
            raise SettingsIncorrectError(
                f"Incorrect configuration: {error}"
            ) from error


# -- Attributes ---------------------------------------------------------------


with as_file(
    files("icotest.config").joinpath("config.yaml")
) as repo_settings_filepath:
    try:
        settings = Settings(default_settings_filepath=repo_settings_filepath)
    except SettingsIncorrectError as settings_incorrect_error:
        print(f"{settings_incorrect_error}", file=stderr)
        sys_exit(1)
    except (ParserError, ScannerError) as parsing_error:
        print(f"Unable to parse configuration: {parsing_error}", file=stderr)
        sys_exit(1)
