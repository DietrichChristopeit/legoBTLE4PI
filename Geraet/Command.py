#  MIT License
#
#  Copyright (c) 2021 Dietrich Christopeit
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.
import threading


class Command:

    def __init__(self, command: bytes, port: int, portFree: threading.Event, withWait: bool = False):
        """

        :param command:
        :param port: int
        :param resultRCV: threading.Event
        :param withWait: bool
        """
        self._command: bytes = command
        self._port: int = port
        self._withWait: bool = withWait
        self._portFree: threading.Event = portFree

    @property
    def command(self) -> bytes:
        return self._command

    @property
    def port(self) -> int:
        return self._port

    @property
    def withWait(self) -> bool:
        return self._withWait

    @property
    def portFree(self) -> threading.Event:
        return self.portFree

