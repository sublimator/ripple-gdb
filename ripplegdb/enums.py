#################################### IMPORTS ###################################

# Std Libs
import functools
import re

from collections import OrderedDict

# Gdb
import gdb

# Us
from ripplegdb.libcpp import StdMapPrinter
from ripplegdb.values import iterate_vector

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

def try_add_commands(d):
    # Errrrkk .... :(
    handlers = gdb.parse_and_eval("_ZN6ripple3RPC12_GLOBAL__N_18HANDLERSE")
    found = re.findall('\["(\w+)"\] = \{.*?'
                        'role_ = ripple::Config::(\w+).*?'
                        'condition_ = ripple::RPC::(\w+)'
                        '.*?\}', str(handlers), re.DOTALL | re.MULTILINE)

    d['commands'] = OrderedDict((t[0], dict(role=t[1],
                                            condition=t[2])) for t in found)

def unique_ptr_get(val):
    return val['_M_t']['_M_head_impl'].dereference()

def get_formats(format_type, entry_type, is_pointer=False):
    # We use the rad iterator from here

    # we can't seem to parse_and_eval so we use this lame hack ;)
    formats = gdb.parse_and_eval('ripple::%s::getInstance()' % format_type)
    # formats = gdb.history(-1)

    if is_pointer:
        formats = formats.dereference()

    # Here we are by name
    # std::map<std::string, Item*>;
    std__map = formats['m_names']

    Item = gdb.lookup_type('ripple::%s::Item' % format_type) .pointer()

    formats = OrderedDict()
    for i, it in enumerate(StdMapPrinter('crap', std__map).children()):
        if i % 2 == 0:
            key = pstd_string(it[1])
            vals = formats[key] = OrderedDict()
        else:
            value = it[1].cast(Item).dereference()
            nth = str(value['m_type'])

            vals[entry_type] =  nth.replace('ripple::', '')
            fields = vals['fields'] = OrderedDict()

            for val in iterate_vector(value['elements']['mTypes']):
                element = unique_ptr_get(val)
                flags = str(element['flags']).replace('ripple::', '')
                field = pstd_string(element['e_field'].referenced_value()['fieldName'])
                fields[field] = flags

    return formats

def all_enums():
    metas = get_SFields_meta_enum()

    d = OrderedDict()
    d['LedgerEntryType'] = symbolic_enum('ripple::LedgerEntryType')
    d['TransactionType'] = symbolic_enum('ripple::TxType')
    d['SerializedTypeID'] = symbolic_enum('ripple::SerializedTypeID')

    d['SOE_Flags'] = symbolic_enum('ripple::SOE_Flags')
    d['transactions'] = get_formats('TxFormats', 'TransactionType')
    d['ledger_entries'] = get_formats('LedgerFormats', 'LedgerEntryType',
                                    is_pointer=1)

    #d['commands'] =
    try_add_commands(d)
    d['TransactionEngineResult'] = get_TER()
    d['SField_Meta_enum'] = metas

    def flagit(n):
        if n == metas['sMD_Default']:
            return

        if n == metas['sMD_Never']:
            return ['sMD_Never']

        return [k for k in metas if k != 'sMD_Default' and n & metas[k]]

    d['field_defaults'] = dict(meta=['sMD_Default'], is_signing_field=True)
    d['fields'] = get_SFields(meta=flagit)

    return d