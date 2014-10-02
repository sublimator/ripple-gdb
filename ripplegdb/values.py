#################################### IMPORTS ###################################

import gdb

#################################### HELPERS ###################################

def read_value(val, n=None):
    return (gdb.selected_inferior()
               .read_memory(
                    val.address, n or val.type.sizeof))

def read_blob(val):
    return bytes(map(int, iterate_vector(val)))

def iterate_vector(vec):
    impl = vec['_M_impl']
    start = impl['_M_start']
    for i in range(int(impl['_M_finish'] - start)):
        yield (start + i).dereference()
