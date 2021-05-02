# coding=utf-8
"""
    A right prompt try.
    
"""
from prompt_toolkit import prompt
from prompt_toolkit.styles import Style
from prompt_toolkit import formatted_text
from sys import platform

example_style = Style.from_dict({
        'rprompt': 'bg:#ff0066 #ffffff',
        })


def get_rprompt(msg: str = None):
    if msg is not None:
        return msg
    
    return platform


if __name__ == '__main__':
    answer = prompt('> ', rprompt=get_rprompt('DISPLAYING PLATFORM SOON...'), style=example_style)
    prompt(f"THE INPUT WAS: {answer}", rprompt=get_rprompt(answer), style=example_style)
    
