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
from ripplegdb.helpers import Proxy, hex_encode, moneyfmt
from ripplegdb.types import STI_TO_TYPE_MAPPING, SerializedType
from ripplegdb.values import read_value, iterate_vector, read_vector

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
    pn = read_vector(val['value'])
    return pAccountID({'pn': pn},read_value=lambda v: v)

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
""" % Proxy(val, uQuality=pQuality, nodes_= NodeList)

def NodeList(val):
    return ''.join(pNode(n, i) for i,n in enumerate(iterate_vector(val)))

def path_state_flags(val):
    flags = int(str(val))
    yeah = dict(account=0x01, currency=0x10, issuer=0x20)
    human = '|'.join(k for k in sorted(yeah) if flags & yeah[k])
    return human

def iterate_stobject_fields(val):
    # mData is a boost::ptr_vector implemented via std::vector `c_`
    for ptr in iterate_vector(val['mData']['c_']):
        st_ptr = ptr.cast(SerializedType.pointer())
        field = st_ptr.dereference()['fName'].dereference()
        typeImpl = STI_TO_TYPE_MAPPING.get(str(field['fieldType']))

        if typeImpl is not None:
            sub_ptr = typeImpl.pointer()
            casted = st_ptr.cast(sub_ptr)
            if casted != 0 and st_ptr.dynamic_cast(sub_ptr):
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

def pNode(val, index=None):
    # We should eventually use some kind of kick arse indentation aware templat
    # ing language.

    # tr: %(transferRate_)s
    #    revRedeem:  %(saRevRedeem)s
    #     revIssue:  %(saRevIssue)s
    #   revDeliver:  %(saRevDeliver)s
    #  saFwdRedeem:  %(saFwdRedeem)s
    #   saFwdIssue:  %(saFwdIssue)s
    # saFwdDeliver:  %(saFwdDeliver)s
    # saOfferFunds:  %(saOfferFunds)s
    #  saTakerPays:  %(saTakerPays)s
    #  saTakerGets:  %(saTakerGets)s

    return ("""
       ix: {ix}
        t: %(uFlags)s
        a: %(account_)s
      c/i: %(currency_)s/%(issuer_)s

      ofr: %(offerIndex_)s %(sleOffer)s

""".format(ix=index)) % Proxy(val,
        sleOffer=node_offer,
        uFlags=path_state_flags)

def pSTObject(value):
    return pLedgerEntry(value)

def pSTArray(value):
    return "TODO: STArray"

def pSTPathSet(value):
    return "TODO: STPathSet"

def pSTVector256(value):
    return repr(list(map(str, iterate_vector(value['mValue'])))).replace("'", '')

def pSTVariableLength(value):
    return value['value']

class RipplePrinter(gdb.printing.PrettyPrinter):
    on = True

    aliases = {
        'ripple::uint160' : pUint160,
        'ripple::Account' : pAccountID,
        'ripple::Currency' : pCurrency,
        'ripple::path::Account' : pAccountID,
        'ripple::path::Currency' : pCurrency,

        'ripple::base_uint<256ul, void>' : pUintAll,
        'ripple::uint256' : pUintAll,
        'ripple::Blob' : lambda v: hex_encode(bytes(read_vector(v['value']))),

        'ripple::STAmount':   pSTAmount,
        'ripple::STAccount':  pSTAccount,
        'ripple::STHash256':  lambda o: pUintAll(o['value']),
        'ripple::STHash160':  lambda o: pUint160(o['value']),
        'ripple::STHash128':  lambda o: pUintAll(o['value']),

        'ripple::STUInt8':  lambda o: o['value'],
        'ripple::STUInt16':  lambda o: o['value'],
        'ripple::STUInt32':  lambda o: o['value'],
        'ripple::STUInt64':  lambda o: ("{0:0{1}x}".format(int(o['value']), 16)),

        'ripple::STObject'  : pSTObject,
        'ripple::STArray'  : pSTArray,
        'ripple::STPathSet'  : pSTPathSet,
        'ripple::STVector256'  : pSTVector256,
        'ripple::STVariableLength'  : pSTVariableLength,

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
                try:
                    yield t.target().name, val.dereference()
                except Exception as e:
                    print(e)

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