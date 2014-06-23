#################################### IMPORTS ###################################
# Std Libs
import os
import importlib
import base64
import collections

from decimal import Decimal

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


def moneyfmt(value, places=2, curr='', sep=',', dp='.',
             pos='', neg='-', trailneg=''):
    """Convert Decimal to a money formatted string.

    places:  required number of places after the decimal point
    curr:    optional currency symbol before the sign (may be blank)
    sep:     optional grouping separator (comma, period, space, or blank)
    dp:      decimal point indicator (comma or period)
             only specify as blank when places is zero
    pos:     optional sign for positive numbers: '+', space or blank
    neg:     optional sign for negative numbers: '-', '(', space or blank
    trailneg:optional trailing minus indicator:  '-', ')', space or blank

    >>> d = Decimal('-1234567.8901')
    >>> moneyfmt(d, curr='$')
    '-$1,234,567.89'
    >>> moneyfmt(d, places=0, sep='.', dp='', neg='', trailneg='-')
    '1.234.568-'
    >>> moneyfmt(d, curr='$', neg='(', trailneg=')')
    '($1,234,567.89)'
    >>> moneyfmt(Decimal(123456789), sep=' ')
    '123 456 789.00'
    >>> moneyfmt(Decimal('-0.02'), neg='<', trailneg='>')
    '<0.02>'

    """
    q = Decimal(10) ** -places      # 2 places --> '0.01'
    sign, digits, exp = value.quantize(q).as_tuple()
    result = []
    digits = list(map(str, digits))
    build, next = result.append, digits.pop
    if sign:
        build(trailneg)
    for i in range(places):
        build(next() if digits else '0')
    if places:
        build(dp)
    if not digits:
        build('0')
    i = 0
    while digits:
        build(next())
        i += 1
        if i == 3 and digits:
            i = 0
            build(sep)
    build(curr)
    build(neg if sign else pos)
    return ''.join(reversed(result))