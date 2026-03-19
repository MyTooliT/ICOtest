"""Configuration for pytest"""

# -- Imports ------------------------------------------------------------------

from logging import getLogger
from typing import AsyncGenerator

from pytest import fixture, mark, StashKey, CollectReport
from icotronic.can import Connection, SensorNode, STH, STU
from netaddr import EUI

from icotest.config import settings
from icotest.test.support.mac import convert_mac_base64

# for renaming the output files
import asyncio
import datetime
import os
import shutil

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


async def _connect_with_retry(stu, sensor_node_name, node_class=None):
    """Helper to connect to a sensor node with automatic STU reset on failure"""
    try:
        if node_class:
            async with stu.connect_sensor_node(sensor_node_name, node_class) as node:
                yield node
        else:
            async with stu.connect_sensor_node(sensor_node_name) as node:
                yield node
    except TimeoutError as e:
        if "Unable to connect to sensor" in str(e):
            getLogger().warning(
                "Failed to connect to sensor node '%s': %s. Resetting STU and retrying...",
                sensor_node_name,
                e,
            )
            await stu.reset()
            await asyncio.sleep(3)
            if node_class:
                async with stu.connect_sensor_node(
                    sensor_node_name, node_class
                ) as node:
                    yield node
            else:
                async with stu.connect_sensor_node(sensor_node_name) as node:
                    yield node
        else:
            raise


@fixture
async def sensor_node(stu, sensor_node_name) -> AsyncGenerator[SensorNode, None]:
    """Connect to and disconnect from sensor node"""

    async for node in _connect_with_retry(stu, sensor_node_name):
        yield node


@fixture
async def sth(stu, sensor_node_name) -> AsyncGenerator[STH, None]:
    """Connect to and disconnect from an STH"""

    async for node in _connect_with_retry(stu, sensor_node_name, STH):
        yield node


@fixture
def json_metadata(request):
    """Fixture for JSON metadata (for --json-report)

    Allows tests to add metadata to the JSON report.
    """
    # Use the plugin's internal metadata storage if available
    if hasattr(request.node, "_json_report_extra"):
        metadata_dict = request.node._json_report_extra.setdefault("metadata", {})
    else:
        # Fallback if the plugin is not active
        metadata_dict = {}

    # Standardized measurement recording function
    def record_measurement(
        name, value, unit=None, lower=None, upper=None, description=None
    ):
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

    # Create a proxy object that provides the 'record' helper but doesn't
    # store it in the actual metadata dictionary that gets serialized
    class MetadataProxy(dict):
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


def pytest_sessionfinish(session, exitstatus):
    """Rename the JSON report using sensor node name and MAC address if available"""
    config = session.config
    report_file = config.getoption("--json-report-file")

    if report_file and os.path.exists(report_file):
        mac_b64 = config.stash.get(MAC_STASH_KEY, None)
        if mac_b64:
            # Clean Base64 for filename (replace / and +)
            mac_clean = mac_b64.replace("/", "_").replace("+", "-")

            # Get the sensor node name (Bluetooth call name)
            sensor_name = settings.sensor_node.name

            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
            new_report_name = f"reports/{sensor_name}_{mac_clean}_{timestamp}.json"

            # Use shutil.move for safer cross-filesystem moves
            shutil.move(report_file, new_report_name)
            getLogger().info("Report renamed to: %s", new_report_name)


def pytest_configure(config):

    # Register custom markers
    config.addinivalue_line(
        "markers", "initial_setup: Tests for initial setup (firmware upload, renaming)"
    )
    config.addinivalue_line("markers", "basic: Basic tests (connection, EEPROM, etc.)")
    config.addinivalue_line("markers", "power: Power consumption tests")
    config.addinivalue_line("markers", "sensor: Sensor tests (standard)")
    config.addinivalue_line("markers", "backpack: Tests for boards with BackPack")
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
