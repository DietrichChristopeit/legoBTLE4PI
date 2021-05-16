# coding=utf-8
"""
    legoBTLE.debug.messages
    ~~~~~~~~~~~~~~~~~~~~~~~
    
    This module is an attempt to make the possible output of all the data flowing to and fro more readable.

    :copyright: Copyright 2020-2021 by Dietrich Christopeit, see AUTHORS.rst.
    :license: MIT, see LICENSE.rst for details
"""

from colorama import Fore
from colorama import Style
from colorama import init

from legoBTLE.legoWP.types import C
from legoBTLE.legoWP.types import MESSAGE_STATUS

init(autoreset=True)

H1 = f'{Style.BRIGHT}{Fore.BLUE}'
H2 = f'{Style.BRIGHT}{Fore.GREEN}'
UL = f'\033[4m'


def debug_info_header(header: str, debug: bool):
    header_len = len(header)
    if debug:
        print(f"{Style.BRIGHT}{Fore.BLUE}{' ' * (64 + header_len)}")
        print(f"{Style.BRIGHT}{Fore.BLUE}{3 * '*'}{29 * ' '} {header} {Style.RESET_ALL}{Style.BRIGHT}{Fore.BLUE}{29 * ' '}{3 * '*'}")
    return


def debug_info_footer(footer: str, debug: bool):
    """:meth:`legoBTLE.debug.messages.debug_info_footer`
    Sets the footer of a debug info message when this message is not atomic.
    
    Parameters
    ----------
    footer : str
        the footer text
    debug : bool
        True if text should be display, False otherwise.
        
    Returns
    -------
    
    """
    _footer = footer.replace('\t', 4 * ' ')
    if debug:
        print(f"{C.BOLD}{C.OKBLUE}{C.UNDERLINE}{' ' * (64 + len(_footer))}")
        print(
            f"{C.BOLD}{C.OKBLUE}{C.UNDERLINE}<< < END +.+.+.+.+ END << << << {C.UNDERLINE}{C.WARNING}{_footer}{C.OKBLUE} << < END +.+.+.+.+ END << << <<")
    return


def debug_info_begin(info: str, debug: bool):
    _info = info.replace('\t', 4 * ' ')
    if debug:
        print(f"{C.BOLD}{C.OKBLUE}**    ", _info, f"{C.BOLD} >> >> BEGIN")
    return


def debug_info(info: str, debug: bool):
    _info = info.replace('\t', 4 * ' ')
    if debug:
        print(f"{C.BOLD}{C.OKBLUE}**        ", _info)
    return


def debug_info_end(info: str, debug: bool):
    _info = info.replace('\t', 4 * ' ')
    if debug:
        print(f"{C.BOLD}{C.OKBLUE}**    {C.OKBLUE}", _info, f"{C.BOLD} << << END")
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
    print(f"{C.BOLD}{_status}** PROGRAM MESSAGE:    {_status}", msg, f"{C.BOLD} +.+.+.+")
    return
