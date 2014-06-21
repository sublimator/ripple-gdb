#################################### IMPORTS ###################################

# Std Libs
import functools

# Gdb
import gdb

#################################### HELPERS ###################################

def enummap(name, prefix=None):
    mapping = dict()
    for f in gdb.lookup_type(name).fields():
        symbolic = f.name
        if prefix is not None:
            symbolic = symbolic.replace(prefix, '')
        
        mapping[f.enumval] = symbolic
        mapping[symbolic] = f.enumval
    return mapping

ripple_enum = functools.partial(enummap, prefix='ripple::')

LET = ripple_enum('ripple::LedgerEntryType')
TER = ripple_enum('ripple::TER')
TER = ripple_enum('ripple::SerializedTypeID')