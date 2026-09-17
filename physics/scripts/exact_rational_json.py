"""Lossless rational JSON without disabling Python's decimal-digit safeguard."""
from fractions import Fraction


def encode_fraction(value):
    if not isinstance(value, Fraction):
        raise TypeError('Fraction required')
    try:
        return str(value)  # Preserve existing readable decimal reports.
    except ValueError:
        # Hex conversion is linear-time and exempt from the decimal guard.
        # Keep sign and all bits; this is not a float or scientific approximation.
        return {'fraction_hex': [hex(value.numerator), hex(value.denominator)]}


def decode_fraction(value):
    if isinstance(value, str):
        return Fraction(value)
    if (not isinstance(value, dict) or set(value) != {'fraction_hex'}
            or not isinstance(value['fraction_hex'], list) or len(value['fraction_hex']) != 2):
        raise ValueError('Decimal fraction string or tagged exact hex fraction required')
    parts = value['fraction_hex']
    if any(not isinstance(part, str) or not part.lstrip('-').startswith('0x') for part in parts):
        raise ValueError('Explicit signed hex numerator and positive hex denominator required')
    numerator, denominator = (int(part, 16) for part in parts)
    if denominator <= 0:
        raise ValueError('Positive exact rational denominator required')
    return Fraction(numerator, denominator)


def json_default(value):
    if isinstance(value, Fraction):
        return encode_fraction(value)
    if hasattr(value, 'tolist'):
        return value.tolist()
    raise TypeError('Unsupported exact report value: '+type(value).__name__)
