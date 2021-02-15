import asyncio
import datetime
from random import uniform


def display_uniform(left, right, loop):
    print(f'RANDOM VALUE: {uniform(left, right)}...')
    loop.call_later(uniform(.0001, .001), display_uniform, left, right, loop)
    return


def display_date(end_time, loop):
    print(datetime.datetime.now())
    if (loop.time() + 1.0) < end_time:
        loop.call_later(1, display_date, end_time, loop)
    else:
        loop.stop()
    return


if __name__ == '__main__':

    loop = asyncio.get_event_loop()
    
    # Schedule the first call to display_date()
    end_time = loop.time() + 5.0
    loop.call_soon(display_date, end_time, loop)
    loop.call_soon(display_uniform, .1, 9.32, loop)
    # Blocking call interrupted by loop.stop()
    try:
        loop.run_forever()
    finally:
        loop.close()
