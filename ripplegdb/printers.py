#################################### IMPORTS ###################################

# StdLibs
import functools
import os
import re
import struct
import collections

# Gdb
import gdb
import gdb.types

# Ripplegdb

from ripplegdb.base58 import base58_check_encode
from ripplegdb.helpers import read_value, Proxy, hex_encode
from ripplegdb.types import TYPE_MAPPINGS, serialized_type_ptr

################################### REGISTRY ###################################

try:
    registry
except NameError:
    registry = {}

def register(name="", helper_name=None):
    def from_func(f):
        f.helper_name = helper_name
        registry[name or f.__name__] = f
        return f

    if isinstance(name, collections.Callable):
        f = name
        name = ""
        return from_func(f)
    else:
        return from_func

def get(k, default=None):
    return registry.get(k, default)

def to_str(v):
    return str(v).encode('utf8')

################################################################################

@register(helper_name='Q')
def pQuality(val):
    (rate, ) = struct.unpack_from("Q", read_value(val))
    mantissa = rate & ~ (0xFF << (64 - 8))
    exponent = (rate >> (64 - 8)) - 100
    quality  = mantissa * (10. ** exponent)
    return str(quality)

@register
def pUint160(val, currency=False, read_value=read_value):
    d = read_value(val['pn'])
    non_empties = tuple(i for i in range(len(d)) if d[i] != b'\x00'
                        and (i == 19 or 12 <= i <= 14))

    if non_empties == ():
        return 'XRP' if currency else '0'
    elif non_empties == (19,) and d[19] == b'\x01':
        return '1'
    elif non_empties == (12, 13, 14):
        return str(d[12:12+3], 'ascii')
    elif currency:
        return hex_encode(bytes(d))
    else:
        return base58_check_encode(bytes(d))

pcurrency = functools.partial(pUint160, currency=True)
pAccountID = functools.partial(pUint160, currency=False)

def pSTAccount(val):
    return pAccountID({'pn': val['value']['_M_impl']['_M_start']},
        read_value=functools.partial(read_value, n=20))

def pUintAll(val, read_value=read_value):
    return hex_encode((read_value(val['pn'])))

def pstd_string(val):
    return val['_M_dataplus']['_M_p'].string()

def pSTAmount(val):
    '''

    We calculate a float creating a constructor string, rather than doing
    calculations, that way we don't lose any accuracy.

    '''
    is_native   = val['mIsNative']
    is_negative = val['mIsNegative']
    mantissa    = val['mValue']
    exponent    = -6 if is_native else int(val['mOffset'])
    sign        = '-' if is_negative else '+'

    # build up a list of the components
    # ${sign}${mantissa}e$exponent
    v = float(''.join(map(str, [sign, mantissa, 'e', exponent])))

    field    = pstd_string(val['fName']['rawJsonName'])
    currency = pUint160(val['mCurrency'], currency=True)
    issuer   = pUint160(val['mIssuer'])

    if currency == 'XRP':
        ret = "%s/XRP%s" % (v, '' if issuer == '0' else issuer)
    else:
        ret = "%s/%s/%s" % (v, currency, issuer)

    if field: ret = "%s:(sf%s)" % (ret, field)

    return ret

def pPathState(val):
    return """\n
PathState %(mIndex)s:
    ter:%(terStatus)s: Q:%(uQuality)s
    in:  
        req:%(saInReq)s  
        act:%(saInAct)s 
        pass:%(saInPass)s
    out: 
        req:%(saOutReq)s 
        act:%(saOutAct)s 
        pass:%(saOutPass)s
    nodes:
        %(nodes_)s
""" % Proxy(val, uQuality=pQuality)

def path_state_flags(val):
    flags = int(to_str(val))
    yeah = dict(account=0x01, currency=0x10, issuer=0x20)
    human = '|'.join(k for k in sorted(yeah) if flags & yeah[k])
    return human


def ledger_entry_fields(val):
    fields = dict()

    val = val['_M_ptr']

    if val != 0:
        offer = val = val.dereference()
        vec_impl = val['mData']['c_']['_M_impl']

        start = vec_impl['_M_start']
        for i in range(int(vec_impl['_M_finish'] - start)):
            derp = start + i
            val = derp.dereference().cast(serialized_type_ptr)

            field = val.dereference()['fName'].dereference()
            sub_ptr = TYPE_MAPPINGS.get(str(field['fieldType']))

            if sub_ptr is not None:
                dcasted = val.dynamic_cast(sub_ptr)
                casted = val.cast(sub_ptr)
                if dcasted != 0:
                    fieldName = str(field['fieldName'])[1:-1]
                    fields[fieldName] = casted
            else:
                fields[str(field['fieldName'])] = val.dereference()["_vptr.SerializedType"].dereference()
    return fields

def pLedgerEntryPointer(val):
    fields = ledger_entry_fields(val)
    if fields:
        return '\n'.join("%-20s%s" % (k+':',v.dereference()) for (k,v) in sorted(fields.items()) if v != 0)
    return ''

def pNode(val):
    return """
        t: %(uFlags)s
        a: %(account_)s
      c/i: %(currency_)s/%(issuer_)s

      ofr: %(offerIndex_)s %(sleOffer)s
      
""" % Proxy(val,
        sleOffer=lambda v: '\n\t' + pLedgerEntryPointer(v).replace('\n', '\n\t'),
        currency_=pcurrency,
        uFlags=path_state_flags)


class RipplePrinter(gdb.printing.PrettyPrinter):
    on = True

    aliases = {
        'ripple::base_uint<160ul, void>' : pUint160,
        'ripple::base_uint<160ul, ripple::core::detail::AccountTag>' : pAccountID,
        'ripple::base_uint<160ul, ripple::core::detail::CurrencyTag>' : pcurrency,
        'ripple::base_uint<256ul, void>' : pUintAll,
        'ripple::STAmount':   pSTAmount,
        # 'ripple::STAccount':   pAccountID,
        'ripple::STHash256':  lambda o: pUintAll(o['value']),
        'ripple::STHash160':  lambda o: pUint160(o['value']),
        'ripple::STHash128':  lambda o: pUintAll(o['value']),

        'ripple::STAccount':  pSTAccount,
        'ripple::SerializedLedgerEntry::pointer':  pLedgerEntryPointer,

        'ripple::STUInt8':  lambda o: o['value'],
        'ripple::STUInt16':  lambda o: o['value'],
        'ripple::STUInt32':  lambda o: o['value'],
        'ripple::STUInt64':  lambda o: ("{0:0{1}x}".format(int(o['value']), 16)),

        'ripple::PathState':  pPathState,
        'ripple::path::Node': pNode
    }

    def __init__(self):
        super(RipplePrinter, self).__init__('RipplePrinter')

    def to_string(self):
        (fn, ) = self.fn
        return fn(self.val)

    def __call__(self, val):
        if not RipplePrinter.on: return

        typename = gdb.types.get_basic_type(val.type).tag
        # print("typename", typename, val.type.name)

        if re.match(b"ripple::.*? \*$", to_str(val.type)):
            val = val.dereference()
            typename = str(val.type)

        if val.type.name in self.aliases and not typename in self.aliases:
            typename = val.type.name

        if typename is not None and typename.startswith('ripple::'):
            ripple_type = typename
            fn = self.aliases.get(ripple_type)
            self.fn = (fn, )
            self.val = val
            if fn is not None:
                return self
            else:
                pass

gdb.printing.register_pretty_printer(None, RipplePrinter(), replace=True)