#################################### HELPERS ###################################

from ripplegdb.helpers import read_value

def deref(init):
    path = ["['_M_ptr']"]
    try:
        # import IPython
        # IPython.embed()
        val = init['_M_ptr']
        if val != 0:
            path.append('.dereference()')
            return path, val.dereference()
        else:
            return path, val
    except Exception as e:
        print('dref err',e)
        return ([], init)

def read_vector(val):
    impl = val['_M_impl']
    start = ['_M_start']
    end = ['_M_finish']
    t = start.type.strip_typedefs().target()
    return read_value(start, n = t.sizeof * int(end - start))