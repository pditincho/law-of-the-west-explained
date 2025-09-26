from common_helpers import c_print, print_byte

MASK_8: int = 0xFF

def rol(value: int, carry: int) -> tuple[int, int]:
    new_value = ((value << 1) | carry) & MASK_8
    new_carry = (value >> 7) & 0x01
    return new_value, new_carry


def ror(value: int, carry: int) -> tuple[int, int]:
    new_carry = value & 0x01
    new_value = (value >> 1) | (carry << 7)
    return new_value, new_carry

def rotate_left_and_print(value: int, carry: int, name: str) -> tuple[int, int]:
    return generic_rotate_and_print(value, carry, name, rol, "ROL")

def rotate_right_and_print(value: int, carry: int, name: str) -> tuple[int, int]:
    return generic_rotate_and_print(value, carry, name, ror, "ROR")

def generic_rotate_and_print(
        value: int,
        carry: int,
        name: str,
        operation,
        operation_name: str,
) -> tuple[int, int]:
    c_print(f"{operation_name} {name}")
    value, carry = operation(value, carry)
    print_byte(name, value)
    c_print(f"Carry: {carry}")
    return value, carry
