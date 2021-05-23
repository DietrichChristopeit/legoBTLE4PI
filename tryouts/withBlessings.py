import time

from blessings import Terminal

term = Terminal()
with term.location():
    for i in range(10):
        t = i
        l = len(str(t))
        print(term.move(10, term.height-1) + 'This is', term.underline(str(t)))
        time.sleep(1)
        print(term.move(10, term.height - 1) + 'This is', l*' ')
        print(term.move(10, term.height-1) + 'This is', term.green(term.underline('also')), term.green(term.underline(str(t))))
