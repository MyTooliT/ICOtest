"""Support to get/set the name of a node its Base64 encoded MAC address"""

# -- Imports ------------------------------------------------------------------

from base64 import b64encode
from typing import Union

from netaddr import EUI

# -- Functions ----------------------------------------------------------------


def convert_mac_base64(mac: Union[str, EUI]) -> str:
    """Convert a Bluetooth MAC address to a Base64 encoded text

    Parameters
    ----------

    mac:
        The MAC address

    Returns
    -------

    The MAC address as Base64 encoded string

    Example
    -------

    >>> convert_mac_base64("08:6b:d7:01:de:81")
    'CGvXAd6B'

    """

    return b64encode(EUI(mac).packed).decode()
