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


class Command:
    """The Command class models a Command sent to the Hub as well as the feedback notification following data execution.
    """

    def __init__(self, data: bytes, port: int, withFeedback: bool = True):
        """The data structure for a command which is sent to the Hub for execution.

        :param data:
            The string of bytes comprising the command.
        :param port:
            The port for which the command is issued. It is a convenience attribute, as the port is encoded
            in the commands and result notifications.
        :param withFeedback:
            TRUE: a feedback notification is requested
            FALSE: no feedback notification is requested
        """
        self._data: bytes = data
        self._port: int = port
        self._withFeedback: bool = withFeedback
        return

    @property
    def data(self) -> bytes:
        return self._data

    @property
    def port(self) -> int:
        return self._port

    @property
    def withFeedback(self) -> bool:
        return self._withFeedback
