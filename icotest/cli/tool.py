"""Command line tool for hardware tests"""

# -- Imports ------------------------------------------------------------------

from argparse import ArgumentParser
from logging import basicConfig, getLogger

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

    return parser


# -- Main ---------------------------------------------------------------------


def main() -> None:
    """ICOtest command line tool"""

    parser = create_icotest_parser()
    arguments = parser.parse_args()

    basicConfig(
        level=arguments.log.upper(),
        style="{",
        format="{asctime} {levelname:7} {message}",
    )

    logger = getLogger()
    logger.info("CLI arguments: %s", arguments)

    if arguments.subcommand == "config":
        ConfigurationUtility.open_user_config()


if __name__ == "__main__":
    main()
