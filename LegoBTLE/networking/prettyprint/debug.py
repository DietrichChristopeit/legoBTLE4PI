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
from LegoBTLE.LegoWP.types import C
from LegoBTLE.LegoWP.types import MESSAGE_STATUS


def debug_info_header(heading: str, debug: bool):
    if debug:
        print(f"{C.BOLD}{C.OKBLUE}{C.UNDERLINE}{' ' * (64  + len(heading))}", end=f"{C.ENDC}\r\n")
        print(f"{C.BOLD}{C.OKBLUE}{C.UNDERLINE}>> > BEGIN +.+.+ BEGIN >> >> >>{C.WARNING}{heading}{C.OKBLUE}>> > BEGIN +.+.+ BEGIN >> >> >>", end=f"{C.ENDC}\r\n")
    return


def debug_info_footer(footer: str, debug: bool):
    if debug:
        print(f"{C.BOLD}{C.OKBLUE}{C.UNDERLINE}{' ' * (64 + len(footer))}", end=f"{C.ENDC}\r\n")
        print(f"{C.BOLD}{C.OKBLUE}{C.UNDERLINE}<< < END +.+.+.+.+ END << << << {C.WARNING}{footer}{C.OKBLUE} << < END +.+.+.+.+ END << << <<", end=f"{C.ENDC}\r\n")
    return


def debug_info_begin(info: str, debug: bool):
    if debug:
        print(f"{C.BOLD}{C.OKBLUE}**\t{C.ENDC}{C.OKBLUE}", info, f"{C.BOLD} >> >> BEGIN", end=f"{C.ENDC}\r\n")
    return


def debug_info(info: str, debug: bool):
    if debug:
        print(f"{C.BOLD}{C.OKBLUE}**\t\t{C.ENDC}", info, end=f"{C.ENDC}\r\n")
    return


def debug_info_end(info: str, debug: bool):
    if debug:
        print(f"{C.BOLD}{C.OKBLUE}**\t{C.ENDC}{C.OKBLUE}", info, f"{C.BOLD} << << END", end=f"{C.ENDC}\r\n")
    return


def prg_out_msg(msg: str, type: MESSAGE_STATUS = MESSAGE_STATUS.INFO):
    print(f"{C.BOLD}{C.OKBLUE}**\t{C.ENDC}{C.OKBLUE}", msg, f"{C.BOLD} +.+.+.+", end=f"{C.ENDC}\r\n")
    return
