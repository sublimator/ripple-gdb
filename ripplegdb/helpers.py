#################################### IMPORTS ###################################
# Std Libs
import os
import importlib
import base64
import collections

# Gdb
import gdb

##################################### DOCS #####################################
"""

This module must not have any import time side effects, that make use of the
rippled objfile, as it will not be loaded, when first imported

"""
#################################### HELPERS ###################################

def reload_module(m):
    importlib.reload(m)

def is_rippled(of):
    return os.path.basename(of.filename) == 'rippled'

def rippled_objfile():
    for of in gdb.objfiles():
        if is_rippled(of):
            return of

def rippled_is_loaded():
    return rippled_objfile() is not None

def subscribe(event):
    def do_connect(f):
        event.connect(f)
        return f
    return do_connect

def on_rippled_loaded(once=None):
    def inner(fn):
        rippled = rippled_objfile()

        if rippled:
            fn(rippled)
            if once: return fn

        @subscribe(gdb.events.new_objfile)
        def hook(event):
            was_rippled = is_rippled(event.new_objfile)

            if was_rippled:
                try:
                    fn(event.new_objfile)
                finally:
                    if once:
                        gdb.events.new_objfile.disconnect(hook)
        return lambda: gdb.events.new_objfile.disconnect(hook)

    if isinstance(once, collections.Callable):
        return inner(once)
    else:
        return inner

def post_partial(f, *a, **kw):
    gdb.post_event(functools.partial(f, *a, **kw))

def post_write(s, *args):
    if not '\n' in s: s += '\n'
    gdb.write(s % args, gdb.STDOUT)
    gdb.flush(gdb.STDOUT)

def read_value(val, n=None):
    return (gdb.selected_inferior()
               .read_memory(
                    val.address, n or val.type.sizeof))

class Proxy:
    def __init__(self, v, **kw):
        self.v=v
        self.kw = kw
    def __getitem__(self, k):
        override = self.kw.get(k)
        if isinstance(override, collections.Callable):
            return override(self.v[k])
        elif override is not None:
            return override
        else:
            return self.v[k]

def hex_encode(s):
    return str(base64.b16encode(s), 'ascii')
