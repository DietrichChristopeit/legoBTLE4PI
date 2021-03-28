# coding=utf-8
# **************************************************************************************************
#  MIT License                                                                                     *
#                                                                                                  *
#  Copyright (c) 2021 Dietrich Christopeit                                                         *
#                                                                                                  *
#  Permission is hereby granted, free of charge, to any person obtaining a copy                    *
#  of this software and associated documentation files (the "Software"), to deal                   *
#  in the Software without restriction, including without limitation the rights                    *
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell                       *
#  copies of the Software, and to permit persons to whom the Software is                           *
#  furnished to do so, subject to the following conditions:                                        *
#                                                                                                  *
#  The above copyright notice and this permission notice shall be included in all                  *
#  copies or substantial portions of the Software.                                                 *
#                                                                                                  *
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR                      *
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,                        *
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE                     *
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER                          *
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,                   *
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE                   *
#  SOFTWARE.                                                                                       *
# **************************************************************************************************
from collections import defaultdict

import numpy as np

from LegoBTLE.Device.ADevice import Device
from LegoBTLE.Device.AHub import Hub
from LegoBTLE.LegoWP.types import SI


def connectAndSetNotify(devices: [Device]) -> [defaultdict]:
    """Connects and sends the notification requests for a list of :class:`LegoBTLE.Device.ADevice`.
    
    Args:
        devices ([Device]): The list of Devices that are to be connected.

    Returns:
        A list of command tasks that can directly be executed.

    """
    print(f"IN CONNECT AND SET NOTIFY")
    ret = [{'cmd': d.connect_ext_srv,
            'kwargs': {'waitUntil': (lambda: True) if d == devices[-1] else (lambda: False)},
            'task': {'tp_id': d.DEVNAME, }
            } for d in devices]
    
    ret += [{'cmd': d.GENERAL_NOTIFICATION_REQUEST if isinstance(d, Hub) else d.REQ_PORT_NOTIFICATION,
             'kwargs': {'waitUntil': (lambda: True) if d == devices[-1] else (lambda: False)},
             'task': {'tp_id': d.DEVNAME, }
            } for d in devices]

    print(f"RETURNS: {ret}")
    return ret


async def sinGenerator(n: int = None, start: float = 0, end: float = 0,
                       step: float = 1.0, inSI: SI = SI.DEG):
    """

    Parameters
    ----------
    n : int
        Lalelu
    start :
    end :
    step :
    inSI :

    Returns
    -------

    """
    _in_si = inSI if inSI == SI.DEG else 1.0
    x = start

    if n is None:
        n = np.int_(np.abs(start - end) / (step / SI.RAD))
    # noinspection PyUnresolvedReferences
    samples = np.linspace(start=start, stop=end, num=n)
    for i, v in enumerate(samples):
        yield np.sin(samples[i]), i
    return
