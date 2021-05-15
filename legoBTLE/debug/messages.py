# coding=utf-8
"""
    legoBTLE.debug.messages
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Various attempts to color the output.
    
    :copyright: Copyright 2020-2021 by Dietrich Christopeit, see AUTHORS.rst.
    :license: MIT, see LICENSE.rst for details
"""

from colorama import Back, Fore, Style


def DBR():
    """Message Style
    
    Returns a Style.
    
    Returns
    -------
    style : tuple
        the Style Dim Black Red
    """
    style = (Style.DIM, Fore.BLACK, Back.RED)
    return style


def DBG():
    """Dim Black Green
    
    Returns
    -------
    style : tuple
        The style Dim, Black, Green
    """
    style = (Style.DIM, Fore.BLACK, Back.GREEN)
    return style


def DBY():
    """
    
    Returns
    -------
    style : tuple
        The style Dim, Black, Yellow
    """
    style = (Style.DIM, Fore.BLACK, Back.YELLOW)
    return style


def DBB():
    """

    Returns
    -------
    style : tuple
        The style Dim, Black, Yellow
    """
    style = (Style.DIM, Fore.BLACK, Back.BLUE)
    return style


def BBR():
    """

    Returns
    -------
    style : tuple
        The style Dim, Black, Yellow
    """
    style = (Style.BRIGHT, Fore.BLACK, Back.RED)
    return style


def BBG():
    """

    Returns
    -------
    style : tuple
        The style Dim, Black, Yellow
    """
    style = (Style.BRIGHT, Fore.BLACK, Back.YELLOW)
    return style


def BBY():
    """

    Returns
    -------
    style : tuple
        The style Dim, Black, Yellow
    """
    style = (Style.BRIGHT, Fore.BLACK, Back.GREEN)
    return style


def BBB():
    """

    Returns
    -------
    style : tuple
        The style Dim, Black, Yellow
    """
    style = (Style.BRIGHT, Fore.BLACK, Back.BLUE)
    return style


def MSG(args, doprint: bool = True, msg: str = "", style=(Style.DIM, Fore.BLACK, Back.LIGHTBLUE_EX)):
    """MSG
    
    Prints out a message.
    
    Parameters
    ----------
    args :
        Argument list to print
    doprint : bool
        True if to print, False otherwise.
    msg : str
        Some string.
    style : tuple
        The style tuple.

    Returns
    -------
    None
        Prints to screen.
    """
    if doprint:
        print(style[0] + style[1] + style[2] + msg.format(*args))
        print(Style.NORMAL + Fore.WHITE + Back.BLACK)
