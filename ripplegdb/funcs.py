#################################### IMPORTS ###################################

import gdb
import ripplegdb.printers

################################################################################

def func(name=""):
    def from_func(f):
        class Function(gdb.Function):
            def __init__(self):
                gdb.Function.__init__(self, name or f.__name__)

            def invoke(self, value):
                return f(value)
        Function()
        return f
    return from_func

##################################### FUNCS ####################################

for k, v in ripplegdb.printers.registry.items():
    name = v.helper_name or k
    func(name)(v)

