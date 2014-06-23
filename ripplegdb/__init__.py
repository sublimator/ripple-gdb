#################################### IMPORTS ###################################

# Std Lib
import os
import importlib

#################################### VERSION ###################################

__version__ = '0.0.1'

################################### CONSTANTS ##################################


# Dependency (stable) sorted, ie. don't introduce circular idiocy
MODULE_LOAD_ORDER = '''\
base58
enums
types
values
helpers
printers
commands
funcs
'''

##################################### INIT #####################################
'''

This file must be able to be loaded from both gdb and via the setup.py, where
the gdb module can't be imported.

'''

try:              loaded
except NameError: loaded  = 0

def do_imports():
    mods = ['ripplegdb.%s' % m for m in MODULE_LOAD_ORDER.split()]
    loaded = [importlib.import_module(m) for m in mods]
    return lambda: [importlib.reload(m) for m in loaded]

def init():
    global hook_remover

    from ripplegdb.libcpp import register_libstdcxx_printers
    from ripplegdb.helpers import on_rippled_loaded

    try: hook_remover()
    except NameError: pass
    except Exception as e:
        print('warning: ', e)

    @on_rippled_loaded(once=False)
    def hook_remover(rippled_objfile):
        global loaded
        loaded += 1

        reload_imported = do_imports()

        reloading = loaded > 1
        gdb.write("%soading ripplegdb..." % ('Rel' if reloading else 'L'))

        if reloading: reload_imported()
        else:         register_libstdcxx_printers(None)

        gdb.write("done.\n")

try:
    import gdb
except ImportError as e:
    pass
else:
    init()