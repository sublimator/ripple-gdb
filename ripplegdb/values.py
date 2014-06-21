#################################### HELPERS ###################################

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