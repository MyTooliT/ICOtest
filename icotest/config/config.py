"""Support for changing configuration values for the tests"""

# -- Import -------------------------------------------------------------------

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

# Replace with `universal-startfile` if/after:
#  https://github.com/jacebrowning/universal-startfile/pull/9
# is merged.
from icotronic.utility.open import open_file, UnableToOpenError
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
            "commands.path.linux",
            is_type_of=list,
            condition=partial(element_is_string, name="commands.path.linux"),
        ),
        must_exist(
            "commands.path.mac",
            is_type_of=list,
            condition=partial(element_is_string, name="commands.path.mac"),
        ),
        must_exist(
            "commands.path.windows",
            is_type_of=list,
            condition=partial(element_is_string, name="commands.path.windows"),
        ),
    ]


def sensor_node_validators() -> list[Validator]:
    """Return list of validators for config data below key `sensor_node`"""

    return [
        must_exist(
            "sensor_node.name",
            is_type_of=str,
        ),
        must_exist(
            "sensor_node.supply.voltage.average",
            "sensor_node.supply.voltage.tolerance",
            is_type_of=Real,
        ),
        must_exist(
            "sensor_node.streaming.power.average",
            "sensor_node.streaming.power.tolerance",
            is_type_of=Real,
        ),
    ]


def stu_validators() -> list[Validator]:
    """Return list of validators for config data below key `stu`"""

    return [
        must_exist(
            "stu.firmware.location",
            "stu.firmware.chip",
            is_type_of=str,
        )
    ]


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

        open_file(filepath)

    @classmethod
    def open_user_config(cls):
        """Open the current users configuration file"""

        try:
            cls.open_config_file(cls.user_config_filepath)
        except UnableToOpenError as error:
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
            *stu_validators(),
        )

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
