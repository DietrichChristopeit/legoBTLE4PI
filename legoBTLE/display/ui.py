from prompt_toolkit import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts import ProgressBar

import os
import time
import signal

bottom_toolbar = HTML(' <b>[f]</b> Print "f" <b>[x]</b> Abort.')

# Create custom key bindings first.
kb = KeyBindings()
cancel = [False]


@kb.add('f')
def _(event):
    print('You pressed `f`.')


@kb.add('x')
def _(event):
    " Send Abort (control-c) signal. "
    cancel[0] = True
    os.kill(os.getpid(), signal.SIGINT)


    # Use `patch_stdout`, to make sure that prints go above the
    # application.
    with patch_stdout():
        with ProgressBar(key_bindings=kb, bottom_toolbar=bottom_toolbar) as pb:
            for i in pb(range(800)):
                time.sleep(.01)
                
                # Stop when the cancel flag has been set.
                if cancel[0]:
                    break