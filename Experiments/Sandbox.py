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
from random import uniform


async def waiter(event, nr, sleep):
    print(f'{nr} waiting for it ...')
    await event.wait()
    print(f'{nr}... got it!')
    await asyncio.sleep(uniform(.5, 3.5) * sleep)
    print(f'{nr}... DONE')


def createTL(event):
    tl = []
    tl.append(asyncio.create_task(waiter(event, 0, 2)))
    tl.append(asyncio.create_task(waiter(event, 1, 1)))
    return tl


async def main():
    # Create an Event object.
    loop = asyncio.get_event_loop()
    event = asyncio.Event()
    
    # Spawn a Task to wait until 'event' is set.
    for c in asyncio.as_completed(createTL(event)):
        asyncio.create_task(c)
    
    # Sleep for 1 second and set the event.
    await asyncio.sleep(9)
    event.set()
    
    while not len(asyncio.all_tasks()) == 1:
        await asyncio.sleep(.02)
        
    return

if __name__ == '__main__':
    
    asyncio.run(main())
