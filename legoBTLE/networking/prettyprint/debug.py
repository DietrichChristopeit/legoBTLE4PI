"""
debug.py
========

This module is an attempt to make the possible output of all the data flowing back and fro more readable.

~~~~~~~~~~~~~~~~~~~~~~~~~

"""
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
from _blueman import conn_info
from colorama import init
from colorama import Fore
from colorama import Style
from colorama import Back
from colorama import Cursor

from legoBTLE.legoWP.types import MESSAGE_STATUS
from legoWP.types import C

init(autoreset=True)

header_style = f"{Style.BRIGHT}{Style.UNDER}{Fore.BLUE}"
info_header_style = f"{Style.BRIGHT}{Style.UNDER}{Fore.GREEN}"
info_msg_style = f"{Style.BRIGHT}{Fore.WHITE}"
msg_style = f"{Style.BRIGHT}{Fore.CYAN}"


def debug_info_header(header: str, debug: bool):
    _header = header.replace('\t', 4 * ' ')
    if debug:
        print(f"{header_style}", end="")
        print(f"{header_style}{' ' * (64 + len(_header))}")
        print(f"{header_style}>> > BEGIN +.+.+ BEGIN >> >> >> {_header}{header_style} >> > BEGIN +.+.+ BEGIN >> >> >>")
    return


def debug_info_footer(footer: str, debug: bool):
    _footer = footer.replace('\t', 4 * ' ')
    if debug:
        print(f"{header_style}", end="")
        print(f"{header_style}{' ' * (64 + len(_footer))}")
        print(
            f"{header_style}<< < END +.+.+.+.+ END << << << {_footer}{header_style} << < END +.+.+.+.+ END << << <<")
    return


def debug_info_begin(info: str, debug: bool):
    _info = info.replace('\t', 4 * ' ')
    if debug:
        print(f"{info_header_style}", end="")
        print(f"{info_header_style}**    {_info}{info_header_style}    >> >> BEGIN")
    return


def debug_info(info: str, debug: bool):
    _info = info.replace('\t', 4 * ' ')
    if debug:
        print(f"{info_msg_style}", end="")
        print(f"{info_msg_style}**        {_info}{info_msg_style}")
    return


def debug_info_end(info: str, debug: bool):
    _info = info.replace('\t', 4 * ' ')
    if debug:
        print(f"{info_header_style}", end="")
        print(f"{info_header_style}**    {_info}{info_header_style}    << << END")
    return


def prg_out_msg(msg: str, m_type: MESSAGE_STATUS = MESSAGE_STATUS.INFO):
    _msg = msg.replace('\t', 4 * ' ')
    print(f"{msg_style}", end="")
    if m_type == MESSAGE_STATUS.INFO:
        _status = Fore.YELLOW
    elif m_type == MESSAGE_STATUS.WARNING:
        _status = Fore.MAGENTA
    elif m_type == MESSAGE_STATUS.FAILED:
        _status = Fore.RED
    else:
        _status = Fore.WHITE
    print(f"{msg_style}{_status}** PROGRAM MESSAGE:    {msg}{msg_style} +.+.+.+")
    return
