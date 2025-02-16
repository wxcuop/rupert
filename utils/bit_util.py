import struct
import ctypes

def get_big_endian(fmt, buf):
    return struct.unpack(f'>{fmt}', buf)[0]

def set_big_endian(fmt, value):
    return struct.pack(f'>{fmt}', value)

def get_little_endian(fmt, buf):
    return struct.unpack(f'<{fmt}', buf)[0]

def set_little_endian(fmt, value):
    return struct.pack(f'<{fmt}', value)

def get_numeric(fmt, buf, is_big_endian):
    return get_big_endian(fmt, buf) if is_big_endian else get_little_endian(fmt, buf)

def set_numeric(fmt, value, is_big_endian):
    return set_big_endian(fmt, value) if is_big_endian else set_little_endian(fmt, value)

def num_set_bits_32(x):
    return bin(x).count('1')

def num_set_bits_64(x):
    return bin(x).count('1')

def rightmost_set_bit(x):
    if x == 0:
        return -1
    return (x & -x).bit_length() - 1

def leftmost_set_bit(x):
    if x == 0:
        return -1
    return x.bit_length() - 1
