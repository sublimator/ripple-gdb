#################################### IMPORTS ###################################

# Std Lib
import os
from pprint import pprint as pp, pformat as pf

# Ggb
import gdb
from gdb import PARAM_ENUM

# Ours
import ripplegdb

################################### CONSTANTS ##################################

PP = ripplegdb.printers.RipplePrinter

################################################################################

def command(name="", class_=gdb.COMMAND_OBSCURE):
    def from_func(f):
        class Command(gdb.Command):
            def __init__(self):
                gdb.Command.__init__(self, name or f.__name__, class_)

            def invoke(self, arg, from_tty):
                f(arg, from_tty)
        Command.__doc__ = f.__doc__
        Command()
        return f
    return from_func

################################### COMMANDS ###################################

@command('rlr')
def reload_ripplegdb(arg, from_tty):
    ripplegdb.helpers.reload_module(ripplegdb)

@command('ipy')
def launch_ipython(arg, from_tty):
    import IPython; IPython.embed()

@command('set ripple-printers')
def set_printer_status(value, from_tty):
    'Enable pretty printers for ripple types when using (p)rint'
    value = value.strip()

    if value == 'toggle':
        PP.on = not PP.on
    elif value:
        PP.on = value.lower() in ('1', 'on', 'true', 'yes')

    print('ripple-printers', 'enabled' if PP.on else 'disabled')

@command('trp')
def toggle_ripple_printers(value, from_tty):
    gdb.execute('set ripple-printers toggle')

@command('reset_term')
def toggle_ripple_printers(value, from_tty):
    os.system('reset')

def deep_items (type_):
    """Return an iterator that recursively traverses anonymous fields.

    Arguments:
        type_: The type to traverse.  It should be one of
        gdb.TYPE_CODE_STRUCT or gdb.TYPE_CODE_UNION.

    Returns:
        an iterator similar to gdb.Type.iteritems(), i.e., it returns
        pairs of key, value, but for any anonymous struct or union
        field that field is traversed recursively, depth-first.
    """
    for k, v in type_.items ():
        if k:
            yield k, v
            if v.is_base_class and v.type: #and (v.type.code in (3,4))
                for i in deep_items (v.type):
                    yield i
        else:
            for i in deep_items (v.type):
                yield i

@command()
def pmembers(arg, from_tty):
    init = gdb.parse_and_eval(arg)
    path, val = ripplegdb.values.deref(init)
    print ("%s.keys() = %s" % (arg, pf(init.type.keys())))
    print (init.type)
    if path:
        pp(list(deep_items(val.type)))
        print ("%s.keys() = %s" % (''.join([arg]+path), pf(val.type.keys())))
    else:
        pp(list(deep_items(init.type)))

