#################################### IMPORTS ###################################

# Std Libs
import functools
import re

from collections import OrderedDict

# Gdb
import gdb

#################################### HELPERS ###################################

def enummap(the_enum, prefix=None, int_keys = True):
    if isinstance(the_enum, str):
        the_enum = gdb.lookup_type(the_enum)

    mapping = OrderedDict()
    for f in sorted(the_enum.fields(), key=lambda f: f.enumval):
        symbolic = f.name
        if prefix is not None:
            symbolic = symbolic.replace(prefix, '')

        if int_keys:
            mapping[f.enumval] = symbolic
        mapping[symbolic] = f.enumval
    return mapping

ripple_enum = functools.partial(enummap, prefix='ripple::')
symbolic_enum = functools.partial(ripple_enum, int_keys=False)

LET = ripple_enum('ripple::LedgerEntryType')
TXT = ripple_enum('ripple::TxType')
TER = ripple_enum('ripple::TER')
STI = ripple_enum('ripple::SerializedTypeID')

################################ RUN TIME ENUMS ################################
'''

These require a running rippled instance to work, and as thus, are exported as
factories.

'''

def pstd_string(val):
    return val['_M_dataplus']['_M_p'].string()

def SField_json(value, meta = lambda v: v):
    f = dict(nth_of_type=int(value['fieldValue']),
             type=int(value['fieldType']))

    m = meta(int(value['fieldMeta']))
    if m is not None:
        f['meta'] = m

    if not bool(value['signingField']):
        f['is_signing_field'] = False

    return f

def get_SFields(meta=lambda v: v):
    fieldsMap = gdb.parse_and_eval("ripple::knownCodeToField")

    def make_dict(items):
        sort_key = lambda i: (i[1]['type'],  i[1]['nth_of_type'])
        return OrderedDict(sorted(items, key=sort_key))

    # Just cheat, and get the values via regex, rather than going rummaging in
    # the map<>
    return make_dict([(f.replace('ripple::sf', ''), SField_json (
                       gdb.parse_and_eval(f), meta=meta)) for f in
                       re.findall('<(ripple::.*)>', str(fieldsMap))])

def get_SFields_meta_enum():
    field_meta_enum = gdb.parse_and_eval("ripple::SField::sMD_Never").type
    return enummap(field_meta_enum, prefix='ripple::SField::', int_keys=False)

def get_TER():
    mapping = OrderedDict()
    for v in sorted([v for v in TER.values() if isinstance(v, int)]):
        token = TER[v]
        human = gdb.parse_and_eval("ripple::transHuman(%s)" % v)
        mapping[token] = ( v, pstd_string(human) )
    return mapping

def all_enums():
    metas = get_SFields_meta_enum()

    d = OrderedDict()
    d['TransactionEngineResult'] = get_TER()
    d['SField_Meta_enum'] = metas
    d['LedgerEntryType'] = symbolic_enum('ripple::LedgerEntryType')
    d['TransactionType'] = symbolic_enum('ripple::TxType')
    d['SerializedTypeID'] = symbolic_enum('ripple::SerializedTypeID')

    def flagit(n):
        if n == metas['sMD_Default']:
            return

        if n == metas['sMD_Never']:
            return ['sMD_Never']

        return [k for k in metas if k != 'sMD_Default' and n & metas[k]]

    d['field_defaults'] = dict(meta=['sMD_Default'], is_signing_field=True)
    d['fields'] = get_SFields(meta=flagit)

    return d