print_enabled = False

def hex_str(h, custom_format):
    return ''.join(custom_format.format(h).upper())

def binary_8(h):
    return f'{h:08b}'

def bits_set_repr(b):
    if b == 0:
        return "Bits set: None"

    s = "Bits set: "
    for i in range(0, 7):
        bit = b & 1
        b >>= 1
        if bit == 1:
            s += str(i) + ","

    s = s[:-1]
    return s

def print_byte(x_name, x):
    c_print(x_name + ": " + hex_str_8(x))

def c_print(s):
    if print_enabled:
        print(s)

def hex_str_8(h):
    return hex_str(h, '{:02x}')

def hex_str_16(h):
    return hex_str(h, '{:04x}')

def read_16_le(data, i):
    return data[i] + (data[i+1] << 8)

def hex_list_8(l):
    s = "["
    for i in range(len(l)):
        s += hex_str_8(l[i])
        s += ", "
    s = s[:-2]
    s += "]"
    return s

def repr_hex_bytes(data, elem_per_row = 16):
    s = ""
    for i in range(0, len(data)):
        if i % elem_per_row == 0:
            s += hex_str_16(i) + ": "

        h = hex_str_8(data[i])
        s += h + " "
        if i % elem_per_row == elem_per_row - 1:
            s += "\n"
    return s

def read_array_8bit(data, base, total):
    a = []
    for i in range (0, total):
        offset = base + i
        data_lo = data[offset]
        a.append(data_lo)
    return a

def read_array_16bit(data, base_lo, base_hi, total):
    a = []
    for i in range (0, total):
        offset_lo = base_lo + i
        offset_hi = base_hi + i
        data_lo = data[offset_lo]
        data_hi = data[offset_hi]
        a.append(data_lo + (data_hi << 8))
    return a

def read_array_16bit_autolength(data, base_lo, base_hi):
    return read_array_16bit(data, base_lo, base_hi, autolength(base_lo, base_hi))

def autolength(a, b):
    if a > b:
        return a - b
    else:
        return b - a

def get_variable_by_name(variables, name):
    return list(filter(lambda v: v.name == name, variables))[0]

def build_label_for_array_element(label, index):
    return label + "[" + str(index) + "]:"
