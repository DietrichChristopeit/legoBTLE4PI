# coding=utf-8
"""
    legoBTLE.legoWP.common_message_header
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The dataclass :class:`COMMON_MESSAGE_HEADER` models the common part for all message coming from the hub brick.

    References
    ----------
        * `LEGO(c) Wireless Protocol 3.0.00r17 <https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#common-message-header>`_
    
    :copyright: Copyright 2020-2021 by Dietrich Christopeit, see AUTHORS.
    :license: MIT, see LICENSE for details
"""

from dataclasses import dataclass, field


# UPS == UPSTREAM === FROM DEVICE
# DNS == DOWNSTREAM === TO DEVICE


@dataclass
class COMMON_MESSAGE_HEADER:
    """This dataclass models the header information common to all LEGO(c) messages.

    For a description of the Common Message Header, `LEGO(c) Wireless Protocol 3.0.00r17
    <https://lego.github.io/lego-ble-wireless-protocol-docs/index.html#common-message-header>`_.

    **The length information is added when the actual message is assembled.**

    """

    data: bytearray = field(init=True)

    def __post_init__(self):
        self.m_length: bytearray = self.data[:1]
        self.hub_id: bytearray = self.data[1:2]
        self.m_type: bytearray = self.data[2:3]

    def __len__(self) -> int:
        return len(self.data)
