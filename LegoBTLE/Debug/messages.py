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
from colorama import Back, Fore, Style

def DBR():
    style = (Style.DIM, Fore.BLACK, Back.RED)
    return style

def DBG():
    style = (Style.DIM, Fore.BLACK, Back.GREEN)
    return style

def DBY():
    style = (Style.DIM, Fore.BLACK, Back.YELLOW)
    return style

def DBB():
    style = (Style.DIM, Fore.BLACK, Back.BLUE)
    return style

def BBR():
    style = (Style.BRIGHT, Fore.BLACK, Back.RED)
    return style

def BBG():
    style = (Style.BRIGHT, Fore.BLACK, Back.YELLOW)
    return style

def BBY():
    style = (Style.BRIGHT, Fore.BLACK, Back.GREEN)
    return style

def BBB():
    style = (Style.BRIGHT, Fore.BLACK, Back.BLUE)
    return style

def MSG(args, doprint: bool=True, msg: str="", style=(Style.DIM, Fore.BLACK, Back.LIGHTBLUE_EX)):
    if doprint:
        print(args)
        print(style[0] + style[1] + style[2]  + msg.format(*args))
        print(Style.NORMAL + Fore.WHITE + Back.BLACK)
