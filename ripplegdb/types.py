#################################### IMPORTS ###################################

import gdb

################################### CONSTANTS ##################################

SerializedType = gdb.lookup_type("ripple::SerializedType")

STAmount = gdb.lookup_type("ripple::STAmount")
STHash256 = gdb.lookup_type("ripple::STBitString<256ul>")
STHash160 = gdb.lookup_type("ripple::STBitString<160ul>")
STAccount = gdb.lookup_type("ripple::STAccount")
STHash128 = gdb.lookup_type("ripple::STBitString<128ul>")
STUInt64 = gdb.lookup_type("ripple::STUInt64")
STUInt32 = gdb.lookup_type("ripple::STUInt32")
STUInt16 = gdb.lookup_type("ripple::STUInt16")
STUInt8 = gdb.lookup_type("ripple::STUInt8")
STObject  =  gdb.lookup_type('ripple::STObject')
STArray  =  gdb.lookup_type('ripple::STArray')
STPathSet  =  gdb.lookup_type('ripple::STPathSet')
STVector256  =  gdb.lookup_type('ripple::STVector256')
STVariableLength = gdb.lookup_type("ripple::STVariableLength")

STI_TO_TYPE_MAPPING = {
    'ripple::STI_UINT8':     STUInt8,
    'ripple::STI_UINT32':    STUInt32,
    'ripple::STI_UINT16':    STUInt16,
    'ripple::STI_UINT64':    STUInt64,
    'ripple::STI_HASH128':   STHash128,
    'ripple::STI_HASH160':   STHash160,
    'ripple::STI_HASH256':   STHash256,
    'ripple::STI_AMOUNT':    STAmount,
    'ripple::STI_ACCOUNT':   STAccount,
    'ripple::STI_VL':        STVariableLength,
    'ripple::STI_OBJECT':    STObject,
    'ripple::STI_ARRAY':     STArray,
    'ripple::STI_PATHSET' :  STPathSet,
    'ripple::STI_VECTOR256': STVector256
}

CODE_LOOKUP = dict([ (getattr(gdb, k), k) for k in dir(gdb) if
                   k.startswith('TYPE_CODE_')])

def lookup_code(c):
    return CODE_LOOKUP[c]