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
TXT = ripple_enum('ripple::TxType')
TER = ripple_enum('ripple::TER')
STI = ripple_enum('ripple::SerializedTypeID')

# from pprint import pprint
# pprint(STI)