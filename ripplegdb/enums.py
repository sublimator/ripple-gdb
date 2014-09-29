#################################### IMPORTS ###################################

# Std Libs
import functools

# Gdb
import gdb

#################################### HELPERS ###################################

def enummap(the_enum, prefix=None, int_keys = True):
    if isinstance(the_enum, str):
        the_enum = gdb.lookup_type(the_enum)

    mapping = dict()
    for f in the_enum.fields():
        symbolic = f.name
        if prefix is not None:
            symbolic = symbolic.replace(prefix, '')

        if int_keys:
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