#################################### IMPORTS ###################################

import gdb

################################### CONSTANTS ##################################

serialized_type = gdb.lookup_type("ripple::SerializedType")

amount = gdb.lookup_type("ripple::STAmount")
hash256 = gdb.lookup_type("ripple::STHash256")
hash160 = gdb.lookup_type("ripple::STHash160")
accountVl = gdb.lookup_type("ripple::STAccount")
hash128 = gdb.lookup_type("ripple::STHash128")
uint64 = gdb.lookup_type("ripple::STUInt64")
uint32 = gdb.lookup_type("ripple::STUInt32")
uint16 = gdb.lookup_type("ripple::STUInt16")
uint8 = gdb.lookup_type("ripple::STUInt8")

VL = gdb.lookup_type("ripple::STVariableLength")

amount_ptr = amount.pointer()
hash256_ptr = hash256.pointer()
hash160_ptr = hash160.pointer()
accountVl_ptr = accountVl.pointer()
hash128_ptr = hash128.pointer()
uint64_ptr = uint64.pointer()
uint32_ptr = uint32.pointer()
uint16_ptr = uint16.pointer()
uint8_ptr = uint8.pointer()
VL_ptr = VL.pointer()
serialized_type_ptr = serialized_type.pointer()

TYPE_MAPPINGS = {
    'ripple::STI_AMOUNT' :  amount_ptr,
    'ripple::STI_HASH160' : hash160_ptr,
    'ripple::STI_ACCOUNT' : accountVl_ptr,
    'ripple::STI_HASH256' : hash256_ptr,
    'ripple::STI_UINT8' :   uint8_ptr,
    'ripple::STI_UINT16' :  uint16_ptr,
    'ripple::STI_UINT32' :  uint32_ptr,
    'ripple::STI_UINT64' :  uint64_ptr,
    'ripple::STI_VL' :  VL_ptr
}


CODE_LOOKUP = dict([ (getattr(gdb, k), k) for k in dir(gdb) if 
                   k.startswith('TYPE_CODE_')])

def lookup_code(c):
    return CODE_LOOKUP[c]
