"""
legoBTLE.ui.view
================

This module holds the UI of the project - :class:`Cockpit`.

It is called and instantiated by :class:`legoBTLE.ui.controller.Control`.

`Cockpit`
    The UI.

"""

import asciimatics


class Cockpit:
    """This is the screen to select devices and make them move.

    Methods
    -------

    display
        display the Screen.
    """

    def __init__(self, gauges: int, title: str = "legoBTLE4PI TUI"):
        self._gauges = gauges
        self.title = title

    def _init(self):
        """Initialization for the screen and the connections to the data providers."""

        return

    def display(self):
        """Display the screen."""

        return
