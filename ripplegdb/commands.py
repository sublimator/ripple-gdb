#################################### IMPORTS ###################################

# Std Lib
import os
import readline
import json

from collections import OrderedDict
from pprint import pprint as pp, pformat as pf
from itertools import takewhile

# Faulthandler
import faulthandler
import sys

# Ggb
import gdb
from gdb import PARAM_ENUM

# Ours
import ripplegdb
from ripplegdb.enums import all_enums

################################### CONSTANTS ##################################

PP = ripplegdb.printers.RipplePrinter

############################### SEGFAULT HANDLING ##############################

# Installs a (perf expensive) trace
if os.environ.get("RIPPLEGDB_FAULTHANDLER") is not None:
    sys.stdout.fileno = lambda: 1
    sys.stderr.fileno = lambda: 2
    faulthandler.enable()

#################################### HEPLERS ###################################

def apply(f): return f()

def command(name='', class_=gdb.COMMAND_OBSCURE):
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
def reload_ripplegdb(arg=None, from_tty=None):
    try:
        ripplegdb.helpers.reload_module(ripplegdb)
    except:
        try:
            delattr(ripplegdb, 'hook_remover')
        finally:
            ripplegdb.helpers.reload_module(ripplegdb)

@command('reset_readline')
def reset_readline(arg=None, from_tty=None):
    readline.set_pre_input_hook()
    readline.set_startup_hook()
    readline.set_completer()
    readline.set_completion_display_matches_hook()
    readline.clear_history()

@command('dump_enums')
def dump_enums(arg=None, from_tty=None):
    '''

    Dumps TxType, TER, LedgerEntryType, and fields to $HOME/rippled-enums.json

    This actually includes information that is stored in static storage maps and
    the like.

    '''
    enums = all_enums()

    with open( os.environ.get('HOME') + '/rippled-enums.json', 'w') as fh:
        json.dump(enums, fh, indent=2)

    print ('OK')

@apply
def launch_ipython():
    try: import IPython
    except ImportError: return

    user_ns= dict (
        rl=reload_ripplegdb,
        luc=ripplegdb.types.lookup_code,
        rv=ripplegdb.values.read_value,
        # You can add whatever to here ;)
        # h = some.longarse.dotted.path,
    )

    ti = IPython.terminal.embed.InteractiveShellEmbed._instance
    if ti is not None:
        for k,v in user_ns.items():
            # fresh meat
            ti.user_ns[k] = v

    @command('ipy')
    def launch_ipython(arg, from_tty):
        import IPython
        n = readline.get_history_length()
        history = (readline.get_history_item(i) for i in
                   range(1, int(1e5) if n == -1 else n))
        history = list(takewhile(lambda v: v is not None, history))
        reset_readline()

        ti = IPython.terminal.embed.InteractiveShellEmbed._instance

        if ti is not None:
            ti.init_readline()
            ti.init_completer()

        gdb.execute('set editing off')
        IPython.embed(user_ns=user_ns, user_module=ripplegdb)
        # Reset the readline, and restore the history
        reset_readline()
        list(map(readline.add_history, history))
        gdb.execute('set editing on')

    return launch_ipython

@command('set ripple-printers')
def set_printer_status(value, from_tty):
    'Enable pretty printers for ripple types when using (p)rint'
    value = value.strip().lower()

    if value == 'toggle':
        PP.on = not PP.on
    elif value:
        PP.on = value in ('1', 'on', 'true', 'yes')

    print('ripple-printers', 'enabled' if PP.on else 'disabled')

@command('trp')
def toggle_ripple_printers(value, from_tty):
    gdb.execute('set ripple-printers toggle')

@command('reset_term')
def toggle_ripple_printers(value, from_tty):
    os.system('reset')
