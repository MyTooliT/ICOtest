"""Command line tool for hardware tests"""

# -- Imports ------------------------------------------------------------------

from argparse import ArgumentParser
from logging import basicConfig, getLogger
from subprocess import run, CalledProcessError
from sys import exit as sys_exit

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

    subparsers.add_parser("run", help="Run tests")

    return parser


def run_pytest(log_level: str, pytest_args: list[str]) -> None:
    """Run pytest for the package using the given arguments

    Args:

        log_level:

            Log level for invocation of pytest

        pytest_args:

            Additional arguments for pytest call

    """

    command = [
        "pytest",
        "--log-cli-level",
        log_level,
        "--pyargs",
        "icotest.test",
    ] + pytest_args
    print(f"\nTest Command:\n\n  {' '.join(command)}\n")
    try:
        run(command, check=True)
    except CalledProcessError as error:
        sys_exit(error.returncode)


# -- Main ---------------------------------------------------------------------


def main() -> None:
    """ICOtest command line tool"""

    parser = create_icotest_parser()
    # Parse known args to get subcommand
    arguments, additional_args = parser.parse_known_args()
    if vars(arguments).get("subcommand", "undefined") != "run":
        arguments = parser.parse_args()

    log_level = arguments.log.upper()
    basicConfig(
        level=log_level,
        style="{",
        format="{asctime} {levelname:7} {message}",
    )

    logger = getLogger(__name__)
    logger.info("CLI arguments: %s", arguments)
    logger.info("Additional unrecognized arguments: %s", additional_args)

    subcommand = arguments.subcommand

    match subcommand:
        case "config":
            ConfigurationUtility.open_user_config()
        case "run":
            run_pytest(log_level, additional_args)


if __name__ == "__main__":
    main()
