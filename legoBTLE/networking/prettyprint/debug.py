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

from colorama import init
from colorama import Fore
from colorama import Style
from colorama import Back
from colorama import Cursor

from legoBTLE.legoWP.types import MESSAGE_STATUS
from legoWP.types import C

init(autoreset=True)

H1 = f'{Style.BRIGHT}{Fore.BLUE}'
H2 = f'{Style.BRIGHT}{Fore.GREEN}'
UL = f'\033[4m'


def debug_info_header(header: str, debug: bool):
    header_len = len(header)
    if debug:
        print(f"{Style.BRIGHT}{Fore.BLUE}{' ' * (64 + header_len)}", end="")
        print(f"{Style.BRIGHT}{Fore.BLUE}{3 * '*'}{29 * ' '} {header} {Style.RESET_ALL}{Style.BRIGHT}{Fore.BLUE}{29 * ' '}{3 * '*'}", end="")
    return


def debug_info_footer(footer: str, debug: bool):
    _footer = footer.replace('\t', 4 * ' ')
    if debug:
        print(f"{C.BOLD}{C.OKBLUE}{C.UNDERLINE}{' ' * (64 + len(_footer))}", end=f"\r\n")
        print(
            f"{C.BOLD}{C.OKBLUE}{C.UNDERLINE}<< < END +.+.+.+.+ END << << << {C.UNDERLINE}{C.WARNING}{_footer}{C.OKBLUE} << < END +.+.+.+.+ END << << <<",
            end=f"{C.ENDC}\r\n")
    return


def debug_info_begin(info: str, debug: bool):
    _info = info.replace('\t', 4 * ' ')
    if debug:
        print(f"{C.BOLD}{C.OKBLUE}**    ", _info, f"{C.BOLD} >> >> BEGIN", end=f"{C.ENDC}\r\n")
    return


def debug_info(info: str, debug: bool):
    _info = info.replace('\t', 4 * ' ')
    if debug:
        print(f"{C.BOLD}{C.OKBLUE}**        ", _info, end=f"{C.ENDC}\r\n")
    return


def debug_info_end(info: str, debug: bool):
    _info = info.replace('\t', 4 * ' ')
    if debug:
        print(f"{C.BOLD}{C.OKBLUE}**    {C.OKBLUE}", _info, f"{C.BOLD} << << END", end=f"{C.ENDC}\r\n")
    return


def prg_out_msg(msg: str, m_type: MESSAGE_STATUS = MESSAGE_STATUS.INFO):
    _msg = msg.replace('\t', 4 * ' ')
    
    if m_type == MESSAGE_STATUS.INFO:
        _status = C.OKBLUE
    elif m_type == MESSAGE_STATUS.WARNING:
        _status = C.WARNING
    elif m_type == MESSAGE_STATUS.FAILED:
        _status = C.FAIL
    else:
        _status = C.OKBLUE
    print(f"{C.BOLD}{_status}** PROGRAM MESSAGE:    {_status}", msg, f"{C.BOLD} +.+.+.+", end=f"{C.ENDC}\r\n")
    return
