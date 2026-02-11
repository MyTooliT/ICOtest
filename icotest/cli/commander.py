"""Support code for Simplicity Commander command line tool

See: https://community.silabs.com/s/article/simplicity-commander

for more information
"""

# -- Imports ------------------------------------------------------------------

from logging import getLogger
from os import environ, pathsep
from pathlib import Path
from platform import system
from re import compile as re_compile
from subprocess import CalledProcessError, run
from sys import byteorder
from typing import Sequence

from icotest.config import settings

# -- Classes ------------------------------------------------------------------


class CommanderException(Exception):
    """Describes problems regarding the execution of Simplicity Commander"""


class CommanderReturnCodeException(CommanderException):
    """A Simplicity Commander command did not return the success status code"""


class CommanderOutputMatchException(CommanderException):
    """The Simplicity Commander output did not contain an expected value"""


class Commander:
    """Wrapper for the Simplicity Commander commandline tool"""

    def __init__(self):

        self._add_path_to_environment()

        self.error_reasons = {
            "programmer not connected": (
                "Programming board is not connected to computer"
            ),
            "device not connected": (
                "Programming board is not connected to device"
            ),
        }

    def _add_path_to_environment(self) -> None:
        """Add path to Simplicity Commander (``commander``) to ``PATH``

        After calling this method you should be able to call ``commander``
        without its path prefix, if you installed it somewhere in the
        locations specified below ``COMMANDS`` → ``PATH`` in the configuration.

        Examples:

            Check that adding the commander path to the environment works

            >>> commander = Commander()

            >>> from subprocess import run
            >>> result = run("commander --version".split(),
            ...              capture_output=True)
            >>> result.returncode == 0
            True

        """

        path = settings.commands.path
        operating_system = system()
        paths = (
            path.linux
            if operating_system == "Linux"
            else path.mac if operating_system == "Darwin" else path.windows
        )

        environ["PATH"] += pathsep + pathsep.join(paths)

    def _run_command(
        self,
        command: list[str],
        description: str,
        possible_error_reasons: list[str] | None = None,
        regex_output: str | None = None,
    ) -> str:
        """Run a Simplicity Commander command

        Args:

            command:
                The Simplicity Commander subcommand including all necessary
                arguments

            description:
                A textual description of the purpose of the command
                e.g. “enable debug mode”

            possible_error_reasons:
                A list of dictionary keys that describe why the command might
                have failed

            regex_output:
                An optional regular expression that has to match part of the
                standard output of the command

        Raises:

            ValueError:

                If ``possible_error_reasons`` is not contained in the
                list of possible error reasons

            CommanderReturnCodeException:

                If the command returned unsuccessfully

            CommanderOutputMatchException:

                If the standard output did not match the optional regular
                expression specified in ``regex_output``

        Returns:

            The standard output of the command

        """

        if possible_error_reasons:
            for reason in possible_error_reasons:
                if reason not in self.error_reasons:
                    raise ValueError(
                        f"“{reason}” is not a valid possible error reason"
                    )

        try:
            getLogger().info(
                "Running command: “commander %s”", " ".join(command)
            )
            result = run(
                ["commander"] + command,
                capture_output=True,
                check=True,
                text=True,
            )
        except CalledProcessError as error:
            # Since Windows seems to return the exit code as unsigned number we
            # need to convert it first to the “real” signed number.
            returncode = (
                int.from_bytes(
                    error.returncode.to_bytes(4, byteorder),
                    byteorder,
                    signed=True,
                )
                if system() == "Windows"
                else error.returncode
            )
            error_message = (
                "Execution of Simplicity Commander command to "
                f"{description} failed with return code "
                f"“{returncode}”"
            )
            combined_output = (
                "\n".join((error.stdout, error.stderr))
                if error.stdout or error.stderr
                else ""
            )
            if combined_output:
                error_message += (
                    "\n\nSimplicity Commander output:\n\n"
                    f"{combined_output.rstrip()}"
                )

            if possible_error_reasons:
                error_reasons = "\n".join([
                    f"• {self.error_reasons[reason]}"
                    for reason in possible_error_reasons
                ])
                error_message += (
                    f"\n\nPossible error reasons:\n\n{error_reasons}"
                )

            raise CommanderReturnCodeException(error_message) from error

        if (
            regex_output is not None
            and re_compile(regex_output).search(result.stdout) is None
        ):
            error_message = (
                "Output of Simplicity Commander command to "
                f"{description}:\n{result.stdout}\n"
                "did not match the expected regular expression "
                f"“{regex_output}”"
            )
            raise CommanderOutputMatchException(error_message)

        return result.stdout

    def enable_debug_mode(self) -> None:
        """Enable debug mode for external device

        Examples:

            Import required library code

            >>> from icotronic.config import settings

            Enable debug mode of STH programming board

            >>> commander = Commander()
            >>> commander.enable_debug_mode()

        """

        error_reasons = ["programmer not connected"]
        self._run_command(
            command="adapter dbgmode OUT".split(),
            description="enable debug mode",
            possible_error_reasons=error_reasons,
            regex_output="Setting debug mode to OUT",
        )

    def unlock_device(self, chip: str) -> None:
        """Unlock device for debugging

        Warning:
            Calling this method will erase the flash of the device!

        Args:

            chip:

                The identifier of the chip on the PCB e.g. “BGM121A256V2”

        """

        self._run_command(
            command="device unlock".split() + ["-d", f"{chip}"],
            description="unlock device",
            possible_error_reasons=[
                "device not connected",
                "programmer not connected",
            ],
            regex_output="Chip successfully unlocked",
        )

    def upload_flash(self, chip: str, filepaths: Sequence[str | Path]) -> None:
        """Upload code into the flash memory of the device

        Args:

            chip:

                The identifier of the chip on the PCB e.g. “BGM121A256V2”

            filepaths:

                A sequence of filepaths that contains images that should be
                uploaded to the device in the given order

        Raises:

            CommanderException:

                If ``filepath`` does not exist or does not point to a valid
                file

        Examples:

            Trying to upload a non existent file causes an error

            >>> commander = Commander()
            >>> # We assume the following file does not exist on your machine
            >>> filepath = "nothing here"
            >>> commander.upload_flash("BGM121A256V2",
            ...     [filepath])  # doctest: +IGNORE_EXCEPTION_DETAIL
            Traceback (most recent call last):
               ...
            CommanderException: Firmware file “nothing here” does not exist

            Trying to upload a directory instead of a file results in an error

            >>> commander.upload_flash("BGM121A256V2",
            ...     [Path.home()]) # doctest: +IGNORE_EXCEPTION_DETAIL
            Traceback (most recent call last):
               ...
            CommanderException: “...” is not a file

        """

        for filepath in filepaths:
            firmware_filepath = Path(filepath)

            if not firmware_filepath.exists():
                raise CommanderException(
                    f"Firmware file “{filepath}” does not exist"
                )

            if not firmware_filepath.is_file():
                raise CommanderException(f"“{filepath}” is not a file")

        # Set debug mode to out, to make sure we flash the STH (connected via
        # debug cable) and not another microcontroller connected to the
        # programmer board.
        self.enable_debug_mode()

        # Unlock device (triggers flash erase)
        self.unlock_device(chip)

        logger = getLogger(__name__)
        for filepath in filepaths:
            self._run_command(
                command=[
                    "flash",
                    f"{firmware_filepath}",
                    "-d",
                    f"{chip}",
                ],
                description="upload firmware",
            )
            logger.info("Uploaded firmware: %s", filepath)

    def read_power_usage(self, seconds: float = 1) -> float:
        """Read the power usage of the connected hardware

        Args:

            seconds:

                The amount of seconds the power usage should be measured for

        Returns:

            The measured power usage in milliwatts

        Raises:

            CommanderOutputMatchException:

                If the function was not able to extract the power usage from
                the output of Simplicity Commander

        Examples:

            Import required library code

            >>> from icotronic.config import settings

            Measure power usage of connected STH

            >>> commander = Commander()
            >>> commander.read_power_usage() > 0
            True

        """

        command = [
            "aem",
            "measure",
            "--windowlength",
            str(round(seconds * 1000)),
        ]

        regex = r"Power\s*\[mW\]\s*:\s*(?P<milliwatts>\d+\.\d+)"
        try:
            output = self._run_command(
                command=command,
                description="read power usage",
                possible_error_reasons=["programmer not connected"],
                regex_output=regex,
            )
        except CommanderOutputMatchException as error:
            raise CommanderOutputMatchException(
                "Unable to extract power usage "
                "from Simplicity Commander output"
            ) from error

        pattern_match = re_compile(regex).search(output)
        assert pattern_match is not None
        milliwatts = pattern_match["milliwatts"]

        return float(milliwatts)


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    from doctest import testmod

    testmod()
