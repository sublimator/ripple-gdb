#################################### IMPORTS ###################################

# Std lib
import os
from os.path import dirname, abspath, normpath, join
from functools import partial

# Gdb
import gdb

WORKING_DIR          = dirname(abspath(__file__))
working_dir_relative = lambda *p: normpath(join(WORKING_DIR, *p))

def on_reload_event(event):
    if event.pathname.endswith('.py'):
        gdb.execute('rlr', from_tty=False)

def create_watcher():
    from pyinotify import WatchManager, Notifier, ThreadedNotifier, \
                          EventsCodes, ProcessEvent, IN_CLOSE_WRITE
    wm = WatchManager()
    mask = IN_CLOSE_WRITE #| EventsCodes.IN_CREATE  # watched events

    class PTmp(ProcessEvent):
        def process_IN_CLOSE_WRITE(self, event):
            def inner(): on_reload_event(event)
            gdb.post_event(inner)

    notifier = ThreadedNotifier(wm, PTmp())
    wdd = wm.add_watch(WORKING_DIR, mask, rec=True)
    notifier.daemon = True # Then our atexit function will work
    notifier.start()
    def on_exited(*e): notifier.stop()
    import atexit
    atexit.register(on_exited)
    return (notifier, wdd)

try:
    notifier
except NameError:
    (notifier, wdd) = create_watcher()