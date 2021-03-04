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
from asyncio import Event, Future
from random import uniform


async def listen(stop: Event, i: int):
    while not stop.is_set():
        print(f"HALLO {i}")
        await asyncio.sleep(uniform(.1, .5))
    return


async def main() -> Future:
    stop: Event = Event()
    stop.clear()
    print("DA")
    await asyncio.wait((asyncio.create_task(listen(stop, 1)),), timeout=.1)
    await asyncio.wait((asyncio.ensure_future(listen(stop, 2)),), timeout=.1)
    print("NOCH DA")
    await asyncio.sleep(5.0)
    print("wieder da")
    await asyncio.sleep(5.0)
    stop.set()
    print("ende")
    await stop.wait()
    f = Future()
    f.set_result(f"Lalles")
    return f


if __name__ == '__main__':
    stop: Event = Event()
    loop = asyncio.get_event_loop()
    fut = asyncio.run(main())
    
    print(f"RESULT: {fut.result()}")
    
   
