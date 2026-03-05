"""Configuration for pytest"""

# -- Imports ------------------------------------------------------------------

from logging import getLogger

from pytest import fixture
from icotronic.can import Connection, SensorNode, STH, STU
from netaddr import EUI

from icotest.config import settings

# for renaming the output files
import datetime
import os

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
async def sensor_node_mac_address(sensor_node_name: str) -> EUI:
    """Return the MAC address of the sensor node used for the test"""

    async with Connection() as stu:
        async with stu.connect_sensor_node(sensor_node_name) as sensor_node:
            return await sensor_node.get_mac_address()


@fixture
async def stu() -> STU:
    """Connect to and disconnect from STU"""

    async with Connection() as stu:
        yield stu


@fixture
async def sensor_node(stu, sensor_node_name) -> SensorNode:
    """Connect to and disconnect from sensor node"""

    async with stu.connect_sensor_node(sensor_node_name) as sensor_node:
        yield sensor_node


@fixture
async def sth(stu, sensor_node_name) -> STH:
    """Connect to and disconnect from an STH"""

    async with stu.connect_sensor_node(sensor_node_name, STH) as sth:
        yield sth


def pytest_configure(config):
    if config.getoption("--json-report", default=False):
        # create a report folder if tht is not yet the case
        if not os.path.exists('reports'):
            os.makedirs('reports')

        # generate a time dependent report name
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
        report_name = f"reports/hardware_test_{timestamp}.json"

        # set the path for the plugin
        config.option.json_report_file = report_name