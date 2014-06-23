#################################### IMPORTS ###################################

# StdLibs
import functools
import os
import re
import struct
import collections

from decimal import Decimal

# Gdb
import gdb
import gdb.types

# Ripplegdb

from ripplegdb.base58 import base58_check_encode
from ripplegdb.helpers import read_value, Proxy, hex_encode, moneyfmt
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
    quality  = float("%se%s" % (mantissa, exponent))
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

pCurrency = functools.partial(pUint160, currency=True)
pAccountID = functools.partial(pUint160, currency=False)

def pSTAccount(val):
    return pAccountID({'pn': val['value']['_M_impl']['_M_start']},
        read_value=functools.partial(read_value, n=20))

def pUintAll(val, read_value=read_value):
    return hex_encode((read_value(val['pn'])))

def pstd_string(val):
    return val['_M_dataplus']['_M_p'].string()


def STAmount_to_decimal(val):
    is_native   = val['mIsNative']
    is_negative = val['mIsNegative']
    mantissa    = val['mValue']
    exponent    = -6 if is_native else int(val['mOffset'])
    sign        = '-' if is_negative else '+'

    # build up a list of the components
    # ${sign}${mantissa}e$exponent
    v = Decimal(''.join(map(str, [sign, mantissa, 'e', exponent])))

    return v

def format_decimal(d):
    return str(d)
    return "%32f" % d
    return moneyfmt(d, places=32)

def pSTAmount(val):
    '''

    We calculate a float creating a constructor string, rather than doing
    calculations, that way we don't lose any accuracy.

    '''
    v = format_decimal(STAmount_to_decimal(val))

    field    = pstd_string(val['fName']['rawJsonName'])
    currency = pCurrency(val['mCurrency'])
    issuer   = pAccountID(val['mIssuer'])

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
""" % Proxy(val, uQuality=pQuality, saInReq=lambda v: v)

def path_state_flags(val):
    flags = int(to_str(val))
    yeah = dict(account=0x01, currency=0x10, issuer=0x20)
    human = '|'.join(k for k in sorted(yeah) if flags & yeah[k])
    return human

def iterate_stobject_fields(val):
    vec_impl = val['mData']['c_']['_M_impl']
    start = vec_impl['_M_start']

    for i in range(int(vec_impl['_M_finish'] - start)):
        ptr = start + i
        st_ptr = ptr.dereference().cast(serialized_type_ptr)
        field = st_ptr.dereference()['fName'].dereference()
        sub_ptr = TYPE_MAPPINGS.get(str(field['fieldType']))

        if sub_ptr is not None:
            dcasted = st_ptr.dynamic_cast(sub_ptr)
            casted = st_ptr.cast(sub_ptr)
            if dcasted != 0 and casted != 0:
                fieldName = pstd_string(field['fieldName'])
                yield (fieldName, casted.dereference())

def pLedgerEntry(val):
    if val.address == 0:
        return
    else:
        fields = sorted(iterate_stobject_fields(val))
        return '\n'.join("%-20s%s" % (k+':',v) for (k,v) in fields )

def pLedgerEntryPointer(val):
    return pLedgerEntry(val['_M_ptr'].dereference())

def node_offer(val):
    v = pLedgerEntryPointer(val)
    if v:
        return '\n\t' + v.replace('\n', '\n\t')
    else:
        return '<empty>'

def pNode(val):
    return """
        t: %(uFlags)s
        a: %(account_)s
      c/i: %(currency_)s/%(issuer_)s
      ofr: %(offerIndex_)s %(sleOffer)s

""" % Proxy(val,
        sleOffer=node_offer,
        currency_=pCurrency,
        uFlags=path_state_flags)


class RipplePrinter(gdb.printing.PrettyPrinter):
    on = True

    aliases = {
        'ripple::uint160' : pUint160,
        'ripple::Account' : pAccountID,
        'ripple::Currency' : pCurrency,
        'ripple::path::Account' : pAccountID,
        'ripple::path::Currency' : pCurrency,

        'ripple::uint256' : pUintAll,

        'ripple::STAmount':   pSTAmount,
        'ripple::STAccount':  pSTAccount,
        'ripple::STHash256':  lambda o: pUintAll(o['value']),
        'ripple::STHash160':  lambda o: pUint160(o['value']),
        'ripple::STHash128':  lambda o: pUintAll(o['value']),

        'ripple::STUInt8':  lambda o: o['value'],
        'ripple::STUInt16':  lambda o: o['value'],
        'ripple::STUInt32':  lambda o: o['value'],
        'ripple::STUInt64':  lambda o: ("{0:0{1}x}".format(int(o['value']), 16)),

        'ripple::SerializedLedgerEntry':  pLedgerEntry,

        'ripple::PathState':  pPathState,
        'ripple::path::Node': pNode
    }

    def __init__(self):
        super(RipplePrinter, self).__init__('RipplePrinter')

    def to_string(self):
        (fn, ) = self.fn
        return fn(self.val)

    def try_types(self, val):
        def fancy():
            t = val.type
            yield t.name, val

            if t.code == gdb.TYPE_CODE_PTR:
                yield t.target().name, val.dereference()

            yield gdb.types.get_basic_type(t).tag, val

        yield from ((k,v) for (k,v) in fancy() if k is not None)

    def __call__(self, val):
        if not RipplePrinter.on: return
        # print("---- RipplePrinter ----")

        for typename, value in self.try_types(val):
            # print("typename", typename)

            if typename is not None:
                ripple_type = typename
                fn = self.aliases.get(ripple_type)
                self.fn = (fn, )
                self.val = val
                if fn is not None:
                    return self
                else:
                    pass

gdb.printing.register_pretty_printer(None, RipplePrinter(), replace=True)