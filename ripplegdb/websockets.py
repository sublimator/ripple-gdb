#################################### IMPORTS ###################################

# Std Lib
import atexit
import os
import time
import sys
import fnmatch
import logging
import subprocess
import threading

from os.path import dirname, abspath, normpath, join
from functools import partial

# Gdb
import gdb

################################### CONSTANTS ##################################

WORKING_DIR          = dirname(abspath(__file__))
working_dir_relative = lambda *p: normpath(join(WORKING_DIR, *p))

#################################### HELPERS ###################################

def different_extension(path, new_ext='.html'):
    folder = os.path.dirname(path)
    fn     = os.path.basename(path)
    f, ext = os.path.splitext(fn)
    return join(folder, f + new_ext)

############################### WEBSOCKET HANDLER ##############################

def on_message(handler, message):
    if 'gdb_command' in message:
        gdb.execute(message.gdb_command, from_tty=True)

def websockets():
    # Tornado for websockets
    import tornado.web
    import tornado.options
    import tornado.ioloop

    from tornado import escape
    from tornado import websocket
    from tornado.util import ObjectDict

    IO = tornado.ioloop.IOLoop.instance()

    class WrappedHandler:
        def __init__(self, io, handler):
            self.io = io
            self.handler = handler

        def send_message(self, message):
            self.io.add_callback(partial(self.handler.send_message, message))

    class GdbRemoteHandler(websocket.WebSocketHandler):
        def get_handler(self):
            if not hasattr(self, 'gdbwrapped'):
                self.gdbwrapped = WrappedHandler(IO, self)
            return self.gdbwrapped

        def allow_draft76(self):
            return True

        def on_close(self):
            pass

        def send_message(self, message):
            try:
                self.write_message(message)
            except:
                logging.error('Error sending message', exc_info=True)

        def on_message(self, message):
            message = ObjectDict(escape.json_decode(message))
            gdb.post_event(partial(on_message, self.get_handler(), message))

    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    handlers = [
        ('/', GdbRemoteHandler),
    ]


    tornado.options.parse_command_line()
    app = tornado.web.Application(handlers=handlers)
    app.listen(40000)

    class IOThread(threading.Thread):
        def run(self):
            IO.start()

    t = IOThread()
    t.daemon = True
    atexit.register(lambda: IO.stop())
    t.start()
    return IO

try:
    server
except NameError:
    server = websockets()
