# coding=utf-8
"""
    This module is used to order the various output of the legoBTLE components and dispolay them in a nicer way.
    
    :copyright:
    :license:
    
"""
import asyncio
from asciimatics.effects import Cycle, Stars
from asciimatics.renderers import FigletText
from asciimatics.scene import Scene
from asciimatics.screen import ManagedScreen, Screen
from typing import List

from legoBTLE.device.ADevice import ADevice


class Telemetrics:
    """Display the output of the components in a mor readable way
    
    .. note:: This is a first try.
    
    """

    def __init__(self, displays: List[ADevice]):
        """Initialize ``Telemetrics``.
        
        Parameters
        ----------
        displays : List[ADevice]
            A List of devices requesting output to be shown.
            
        """
        self._displays = displays
        self._screen: ManagedScreen = ManagedScreen()
        

def update_screen(end_time, loop, screen):
    screen.draw_next_frame()
    if loop.time() < end_time:
        loop.call_later(0.05, update_screen, end_time, loop, screen)
    else:
        loop.stop()

def server_output():
# Define the scene that you'd like to play.
    with ManagedScreen() as screen:
    print_at

# Schedule the first call to display_date()
loop = asyncio.get_event_loop()
end_time = loop.time() + 5.0
loop.call_soon(update_screen, end_time, loop, screen)

# Blocking call interrupted by loop.stop()
loop.run_forever()
loop.close()
screen.close()
