#################################### IMPORTS ###################################

import gdb

#################################### HELPERS ###################################

def read_value(val, n=None):
    return (gdb.selected_inferior()
               .read_memory(
                    val.address, n or val.type.sizeof))

def read_vector(val):
    impl = val['_M_impl']
    start = impl['_M_start']
    end = impl['_M_finish']
    t = start.type.strip_typedefs().target()
    return read_value(start, n = t.sizeof * int(end - start))

def iterate_vector(vec):
    impl = vec['_M_impl']
    start = impl['_M_start']
    for i in range(int(impl['_M_finish'] - start)):
        yield (start + i).dereference()
