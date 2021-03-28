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

import asyncio
from typing import Callable

import numpy as np


from LegoBTLE.LegoWP.types import SI


async def generator(func: Callable = None, n: int = None, start: float = 0, end: float = 0, step: float = 1.0, inSI: SI = SI.DEG):
    """

    Parameters
    ----------
    func : Callable
        the function values to generate
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
        n = np.int_(np.abs(start - end) / (step/SI.RAD))
    # noinspection PyUnresolvedReferences
    samples = np.linspace(start=start, stop=end, num=n)
    for i, v in enumerate(samples):
        yield func(samples[i]), i
    return


async def main():
    """main Function

    """
    async for i in generator(
            func=np.tan,
            start=0.0,
            end=(2*np.pi),
            step=5.0,
            inSI=SI.RAD):
        print(i)


if __name__ == '__main__':

    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(main())

    except KeyboardInterrupt:
        loop.stop()
        pass
