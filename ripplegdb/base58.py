#################################### IMPORTS ###################################

import hashlib
import base64

############################### HASHING FUNCTIONS ##############################

def dhash(s):
    return hashlib.sha256(hashlib.sha256(s).digest()).digest()

def rhash(s):
    h1 = hashlib.new('ripemd160')
    h1.update(hashlib.sha256(s).digest())
    return h1.digest()

def decode_hex(b):
    return base64.b16decode(bytes(b, 'ascii'))

def byte_chr(o):
    return bytes((o,))

################################ BASE58 ENCODING ###############################

alphabet = b'rpshnaf39wBUDNEGHJKLM4PQRST7VWXYZ2bcdeCg65jkm8oFqi1tuvAxyz'

def base58_encode(n):
    l = []
    while n > 0:
        n, r = divmod(n, 58)
        l.append(alphabet[r])
    return bytes(reversed(l))

def base58_encode_padded(s):
    n = int(base64.b16encode(s), 16)
    res = base58_encode(n)
    pad = 0
    for c in s:
        if c == 0:
            pad += 1
        else:
            break
    return bytes([alphabet[0]] * pad) + res

def base58_check_encode(s, version=0):
    vs = bytes((version, )) + s
    check = dhash(vs)[:4]
    return str(base58_encode_padded(vs + check), 'ascii')

def base58_decode(s):
    n = 0
    for ch in s:
        n *= 58
        digit = alphabet.index(ch)
        n += digit
    return n

def base58_decode_padded(s):
    pad = 0
    for c in s:
        if c == alphabet[0]:
            pad += 1
        else:
            break
    h = hex(base58_decode(s))[2:].upper()
    if len(h) % 2: h = '0' + h
    res = decode_hex(h) #.decode('hex')
    return bytes([0] * pad) + res

def base58_check_decode(s, version=0):
    k = base58_decode_padded(bytes(s, 'ascii'))
    v0, data, check0 = k[0:1], k[1:-4], k[-4:]
    check1 = dhash(v0 + data)[:4]
    if check0 != check1:
        raise BaseException('checksum error')
    if version != ord(v0):
        raise BaseException('version mismatch')
    return data

account_1 = (bytes(([0]*19) + [1]))
account_1_base58 = 'rrrrrrrrrrrrrrrrrrrrBZbvji'

assert account_1 == account_1
assert base58_check_encode(account_1) == account_1_base58
assert base58_check_decode(account_1_base58) == account_1