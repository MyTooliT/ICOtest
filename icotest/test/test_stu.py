"""Test STU"""

# -- Imports ------------------------------------------------------------------

from icotronic.can import Connection
from icotronic.can.error import CANInitError

# -- Functions ----------------------------------------------------------------


async def test_connection():
    """Test if connection to STU is possible"""

    message = "Unable to connect to STU"

    try:
        async with Connection():
            assert True, message
    except CANInitError:
        assert False, message
