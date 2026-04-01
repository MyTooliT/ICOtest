"""Command line tool for hardware tests"""

# -- Imports ------------------------------------------------------------------

import logging

from argparse import ArgumentParser
from logging import getLogger, FileHandler, Formatter
from os import environ, makedirs, path
from subprocess import run, CalledProcessError
from sys import exit as sys_exit, executable
from datetime import datetime

from icotronic.cmdline.types import node_name

from icotest.config import ConfigurationUtility

# -- Functions ----------------------------------------------------------------


def create_icotest_parser() -> ArgumentParser:
    """Create command line parser for ICOtest

    Returns:

        A parser for the CLI arguments of icotest

    """

    parser = ArgumentParser(description="ICOtest CLI tool")

    parser.add_argument(
        "--log",
        choices=("debug", "info", "warning", "error", "critical"),
        default="warning",
        required=False,
        help="minimum log level",
    )

    subparsers = parser.add_subparsers(
        required=True, title="Subcommands", dest="subcommand"
    )

    # ==========
    # = Config =
    # ==========

    subparsers.add_parser(
        "config", help="Open configuration file in default application"
    )

    # =======
    # = Run =
    # =======

    run_parser = subparsers.add_parser("run", help="Run tests")
    run_parser.add_argument(
        "-n",
        "--name",
        help="Name of sensor node",
        type=node_name,
    )
    run_parser.add_argument(
        "--test-group",
        choices=["initial", "production", "full", "rename", "flash-only"],
        help=(
            "Predefined test group: "
            "initial=firmware upload+rename, "
            "flash-only=firmware upload only, "
            "production=power+sensors, "
            "full=all except STU, "
            "rename=rename-only recovery test"
        ),
    )
    run_parser.add_argument(
        "--skip-backpack",
        action="store_true",
        help="Skip BackPack tests even if configured",
    )

    return parser


def run_pytest(
    log_level: str,
    pytest_args: list[str],
    environment: dict[str, str],
    log_file: str | None = None,
) -> None:
    """Run pytest for the package using the given arguments

    Args:

        log_level:

            Log level for invocation of pytest

        pytest_args:

            Additional arguments for pytest call

        environment:

            Environment for pytest call

        log_file:

            Path to log file for pytest output

    """

    command = [
        executable,
        "-m",
        "pytest",
        "--log-cli-level",
        log_level,
        "--pyargs",
        "icotest.test",
    ]

    if log_file:
        command.extend(["--log-file", log_file, "--log-file-level", "INFO"])

    command += pytest_args
    print(f"\nTest Command:\n\n  {' '.join(command)}\n")
    try:
        run(command, check=True, env=environment)
    except CalledProcessError as error:
        sys_exit(error.returncode)


# -- Main ---------------------------------------------------------------------


# pylint: disable=too-many-locals, too-many-branches, too-many-statements


def main() -> None:
    """ICOtest command line tool"""

    parser = create_icotest_parser()
    # Parse known args to get subcommand
    arguments, additional_args = parser.parse_known_args()
    if vars(arguments).get("subcommand", "undefined") != "run":
        arguments = parser.parse_args()

    log_level = arguments.log.upper()

    # Configure root logger
    logger_root = getLogger()
    logger_root.setLevel(log_level)

    log_format = Formatter("{asctime} {levelname:7} {message}", style="{")

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    logger_root.addHandler(console_handler)

    # Ensure reports directory exists for logs
    if not path.exists("reports"):
        makedirs("reports")

    # File handler for production audit trail
    log_file_path = (
        f"reports/icotest_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.log"
    )
    file_handler = FileHandler(log_file_path, encoding="utf-8")
    file_handler.setFormatter(log_format)
    logger_root.addHandler(file_handler)

    logger = getLogger(__name__)
    logger.info("CLI arguments: %s", arguments)
    logger.info("Log file created at: %s", log_file_path)
    logger.info("Additional unrecognized arguments: %s", additional_args)

    subcommand = arguments.subcommand

    match subcommand:
        case "config":
            ConfigurationUtility.open_user_config()
        case "run":
            environment_pytest = dict(environ)
            pytest_markers = []

            if arguments.name is not None:
                logger.info("Using sensor node name: %s", arguments.name)
                environment_pytest["DYNACONF_SENSOR_NODE__NAME"] = (
                    arguments.name
                )

            # Process test groups
            if hasattr(arguments, "test_group") and arguments.test_group:
                if arguments.test_group == "initial":
                    pytest_markers.extend(["-m", "initial_setup"])
                    logger.info("Running initial setup tests")
                    # Auto-enable JSON report for initial tests
                    if "--json-report" not in additional_args:
                        additional_args.append("--json-report")
                elif arguments.test_group == "production":
                    pytest_markers.extend(["-m", "power or sensor"])
                    logger.info("Running production tests (power + sensors)")
                    # Auto-enable JSON report for production tests
                    if "--json-report" not in additional_args:
                        additional_args.append("--json-report")

                    # Include backpack tests if backpack is configured
                    if not arguments.skip_backpack:
                        pytest_markers[-1] += " or backpack"
                        logger.info("Including BackPack tests")
                elif arguments.test_group == "full":
                    pytest_markers.extend(["-m", "not stu"])
                    logger.info("Running full tests (without STU)")
                    # Auto-enable JSON report for full tests
                    if "--json-report" not in additional_args:
                        additional_args.append("--json-report")
                elif arguments.test_group == "rename":
                    pytest_markers.extend(["-m", "rename"])
                    logger.info("Running rename-only (Base64 naming) tests")
                    if "--json-report" not in additional_args:
                        additional_args.append("--json-report")
                elif arguments.test_group == "flash-only":
                    pytest_markers.extend(["-m", "initial_firmware_only"])
                    logger.info("Running firmware-only flash tests")
                    if "--json-report" not in additional_args:
                        additional_args.append("--json-report")

            # Skip BackPack tests if explicitly requested via --skip-backpack
            skip_backpack = (
                hasattr(arguments, "skip_backpack") and arguments.skip_backpack
            )

            if skip_backpack and "backpack" in pytest_markers[-1]:
                logger.info("Skipping BackPack tests")
                # Remove "or backpack" from production group marker
                pytest_markers[-1] = pytest_markers[-1].replace(
                    " or backpack", ""
                )

            # Determine log file for this run
            test_log_file = log_file_path.replace(".log", "_pytest.log")

            run_pytest(
                log_level,
                additional_args + pytest_markers,
                environment_pytest,
                log_file=test_log_file,
            )


# pylint: enable=too-many-locals, too-many-branches, too-many-statements

if __name__ == "__main__":
    main()
