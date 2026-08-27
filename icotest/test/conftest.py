"""Configuration for pytest"""

# -- Imports ------------------------------------------------------------------

import datetime
import os
import shutil

from logging import getLogger
from typing import AsyncGenerator

from pytest import fixture, StashKey
from icotronic.can import Connection, SensorNode, STH, STU
from netaddr import EUI

from icotest.config import settings
from icotest.test.support.mac import convert_mac_base64

# Stash key for the MAC address
MAC_STASH_KEY = StashKey[str]()

# pylint: disable=redefined-outer-name

# -- Fixtures -----------------------------------------------------------------


@fixture(scope="session")
def anyio_backend():
    """Set default async backend"""

    return "asyncio"


@fixture(scope="session")
def sensor_node_name() -> str:
    """Returns the name of the sensor node used for the test"""

    getLogger().info("Using sensor node name: %s", settings.sensor_node.name)

    return settings.sensor_node.name


@fixture(scope="session")
async def sensor_node_mac_address(request, sensor_node_name: str) -> EUI:
    """Return the MAC address of the sensor node used for the test"""

    async with Connection() as stu:
        async with stu.connect_sensor_node(sensor_node_name) as sensor_node:
            mac = await sensor_node.get_mac_address()
            # Stash the MAC address for later renaming
            mac_b64 = convert_mac_base64(mac)
            request.config.stash[MAC_STASH_KEY] = mac_b64
            return mac


@fixture
async def stu() -> AsyncGenerator[STU, None]:
    """Connect to and disconnect from STU"""

    async with Connection() as stu:
        yield stu


@fixture
async def sensor_node(
    stu, sensor_node_name
) -> AsyncGenerator[SensorNode, None]:
    """Connect to and disconnect from sensor node"""

    async with stu.connect_sensor_node(sensor_node_name) as sensor_node:
        yield sensor_node


@fixture
async def sth(stu, sensor_node_name) -> AsyncGenerator[STH, None]:
    """Connect to and disconnect from an STH"""

    async with stu.connect_sensor_node(sensor_node_name, STH) as sth:
        yield sth


@fixture
def json_metadata(request):
    """Fixture for JSON metadata (for --json-report)

    Allows tests to add metadata to the JSON report.
    """
    # Use the plugin's internal metadata storage if available
    if hasattr(request.node, "_json_report_extra"):
        # pylint: disable=protected-access
        metadata_dict = request.node._json_report_extra.setdefault(
            "metadata", {}
        )
        # pylint: enable=protected-access
    else:
        # Fallback if the plugin is not active
        metadata_dict = {}

    # pylint: disable=too-many-arguments, too-many-positional-arguments

    def record_measurement(
        name, value, unit=None, lower=None, upper=None, description=None
    ):
        """Standardized measurement recording function"""
        measurement = {"value": value}
        if unit:
            measurement["unit"] = unit
        if lower is not None:
            measurement["lower_limit"] = lower
        if upper is not None:
            measurement["upper_limit"] = upper
        if description:
            measurement["description"] = description
        metadata_dict[name] = measurement

    # pylint: enable=too-many-arguments, too-many-positional-arguments

    class MetadataProxy(dict):
        """Create a proxy object that provides the 'record' helper but doesn't
        store it in the actual metadata dictionary that gets serialized"""

        def __getitem__(self, key):
            if key == "record":
                return record_measurement
            return super().__getitem__(key)

        def __setitem__(self, key, value):
            metadata_dict[key] = value

        def update(self, *args, **kwargs):
            metadata_dict.update(*args, **kwargs)

        def setdefault(self, key, default=None):
            return metadata_dict.setdefault(key, default)

        def pop(self, key, default=None):
            return metadata_dict.pop(key, default)

    return MetadataProxy(metadata_dict)


def pytest_sessionfinish(
    session, exitstatus  # pylint: disable=unused-argument
):
    """Rename the JSON report using the MAC address if available"""
    config = session.config
    report_file = config.getoption("--json-report-file")

    if report_file and os.path.exists(report_file):
        mac_b64 = config.stash.get(MAC_STASH_KEY, None)
        if mac_b64:
            # Clean Base64 for filename (replace / and +)
            mac_clean = mac_b64.replace("/", "_").replace("+", "-")

            # Identify node type (STH, SMH, etc.)
            node_type = settings.get("sensor_node.type", "ICOtronic")

            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
            new_report_name = (
                f"reports/{node_type}_{mac_clean}_{timestamp}.json"
            )

            # Use shutil.move for safer cross-filesystem moves
            shutil.move(report_file, new_report_name)
            getLogger().info("Report renamed to: %s", new_report_name)


def pytest_configure(config):
    """Perform initial configuration"""

    # Register custom markers
    config.addinivalue_line(
        "markers",
        "initial_setup: Tests for initial setup (firmware upload, renaming)",
    )
    config.addinivalue_line(
        "markers", "basic: Basic tests (connection, EEPROM, etc.)"
    )
    config.addinivalue_line("markers", "power: Power consumption tests")
    config.addinivalue_line("markers", "sensor: Sensor tests (standard)")
    config.addinivalue_line(
        "markers", "backpack: Tests for boards with BackPack"
    )
    config.addinivalue_line("markers", "stu: STU-specific tests")

    if config.getoption("--json-report", default=False):
        # Create a report folder if it does not yet exist
        if not os.path.exists("reports"):
            os.makedirs("reports")

        # Generate a time-dependent report name
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
        report_name = f"reports/hardware_test_{timestamp}.json"

        # Set the path for the plugin
        config.option.json_report_file = report_name
