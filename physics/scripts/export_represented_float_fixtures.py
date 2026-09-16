"""Exact-rational FP32 arithmetic/admissibility fixtures, not solver acceptance."""
import argparse
from fractions import Fraction
import hashlib
import json
from math import isqrt
from pathlib import Path
import struct
import numpy as np


def rounded_bits(value):
    """Round a finite rational to IEEE binary32, nearest/even, without FP math."""
    sign = 0x80000000 if value < 0 else 0
    value = abs(value)
    if not value: return sign
    n, d = value.numerator, value.denominator
    exponent = n.bit_length()-d.bit_length()
    if (n < (d << exponent)) if exponent >= 0 else ((n << -exponent) < d): exponent -= 1
    shift = max(exponent-23, -149)
    numerator, denominator = (n, d << shift) if shift >= 0 else (n << -shift, d)
    quotient, remainder = divmod(numerator, denominator)
    if 2*remainder > denominator or (2*remainder == denominator and quotient & 1): quotient += 1
    if quotient == 0: return sign
    if quotient >= 1 << 24: quotient >>= 1; exponent += 1
    if exponent > 127: return sign | 0x7f800000
    if exponent < -126 and quotient < 1 << 23: return sign | quotient
    return sign | ((max(exponent, -126)+127) << 23) | (quotient & 0x7fffff)


def cases():
    # Actual rejected y79/x88 Euler depth, and its retained momentum.
    yield 'captured_depth', (1.1754943508222875e-38, 1.5894572769070692e-8, -1.0336046977263681e-37)
    yield 'captured_momentum', (5.168023488631841e-38, 1.5894572769070692e-8, -4.544210029657536e-37)
    for bits in (0, 1, 2, 3, 0x3fffff, 0x7fffff, 0x800000, 0x800001, 0x1000000, 0x3f800000, 0x7f7fffff):
        value = struct.unpack('<f', struct.pack('<I', bits))[0]
        for sign in (1, -1):
            yield f'roundtrip_{bits:x}_{sign}', (sign*value, 1., 0.)
    tiny = 2.**-149
    for s, dt, r in ((tiny, .5, -tiny), (2*tiny, .5, -tiny), (3*tiny, .5, -tiny),
                     (0, .5, tiny), (0, .75, tiny), (0, .25, tiny), (1, 1, -1),
                     (2.**-126, .5, -tiny), (2.**-126, 1, -tiny)):
        yield 'tie_or_cancellation', (s, dt, r)
    for sign in (1, -1):
        yield 'double_rounding_odd_tie', (-sign*2.**-60, 1+2.**-23, sign*1.5)
        yield 'double_rounding_even_tie', (sign*2.**-60, 1+3*2.**-23, sign*1.5)
    rng = np.random.default_rng(818013)
    raw = rng.integers(0, 0xffffffff, (4096, 3), dtype=np.uint32)
    raw[(raw & 0x7f800000) == 0x7f800000] &= np.uint32(0xff7fffff)
    for row in raw.view(np.float32): yield 'finite_random', tuple(map(float, row))


def rk2_cases():
    tiny = 2.**-149
    for sign in (1, -1):
        for h in (tiny, 2*tiny, 3*tiny, 2.**-126, 1., 2.**120):
            yield 'constant', (sign*h, sign*h, .001, 0.)
        # Cancellation must reveal the tiny third term even when the other
        # two terms are hundreds of bits larger. No intermediate FP rounding.
        for huge in (1., 2.**100):
            for film in (2*tiny, 4*tiny, 2.**-126):
                yield 'deep_cancellation', (sign*film, huge, 1., -huge)
                yield 'deep_cancellation_swapped', (huge, sign*film, 1., -huge)
    yield 'captured_candidate', (2.**-126, float(np.nextafter(np.float32(2.**-126), np.float32(0))),
                                 1.5894572769070692e-8, -1.0336046977263681e-37)
    rng = np.random.default_rng(373831)
    raw = rng.integers(0, 0xffffffff, (8192, 4), dtype=np.uint32)
    raw[(raw & 0x7f800000) == 0x7f800000] &= np.uint32(0xff7fffff)
    for row in raw.view(np.float32): yield 'finite_random', tuple(map(float, row))


def valid_state(values):
    h, x, y, foam = map(float, values)
    if not all(np.isfinite(values)) or h < 0 or foam < 0: return False
    if h == 0: return x == 0 and y == 0
    return all((rounded_bits(Fraction(v)/Fraction(h)) & 0x7f800000) != 0x7f800000 for v in (x,y))


def validity_cases():
    tiny = 2.**-149; largest = float(np.finfo(np.float32).max)
    for h in (0., tiny, 2.**-126, 1., largest):
        for momentum in (0., tiny, 4*tiny, 1., largest):
            for sign in (1,-1): yield 'represented_velocity', (h,sign*momentum,-sign*momentum,0.)
    for values in ((tiny,tiny,0,-tiny),(-tiny,0,0,0),(0,tiny,0,0),(tiny,0,0,tiny),
                   (np.inf,0,0,0),(1,np.nan,0,0),(1,0,np.inf,0),(1,0,0,np.nan)):
        yield 'invalid_or_thin_foam', values
    rng = np.random.default_rng(37707)
    raw = rng.integers(0, 0xffffffff, (8192,4), dtype=np.uint32)
    for row in raw.view(np.float32): yield 'finite_random', tuple(map(float,row))


def divided_bits(numerator, denominator):
    a,b=(struct.unpack('<I',struct.pack('<f',v))[0] for v in (numerator,denominator))
    sign=(a^b)&0x80000000
    n,d=a&0x7fffffff,b&0x7fffffff
    if n>0x7f800000 or d>0x7f800000 or n==d==0x7f800000 or n==d==0:return 0x7fc00000
    if n==0x7f800000 or d==0:return sign|0x7f800000
    if d==0x7f800000 or n==0:return sign
    return rounded_bits(Fraction(float(numerator))/Fraction(float(denominator)))


def division_cases():
    tiny=2.**-149;largest=float(np.finfo(np.float32).max)
    yield 'captured_velocity',(5.168022928112455e-38,1.1754942106924411e-38,0.,0.)
    for n in (0.,-0.,tiny,2*tiny,3*tiny,2.**-126-tiny,2.**-126,1.,largest,np.inf,np.nan):
        for d in (0.,-0.,tiny,2*tiny,3*tiny,2.**-126,1.,largest,np.inf,np.nan):
            for sign in (1,-1):yield 'range_and_special',(sign*n,d,0.,0.)
    for exponent in range(-149,128):
        yield 'self_ratio',(2.**exponent,2.**exponent,0.,0.)
        yield 'subnormal_halfway',(tiny,2.,0.,0.)
    rng=np.random.default_rng(991737)
    raw=rng.integers(0,0xffffffff,(16384,2),dtype=np.uint32)
    raw[(raw&0x7f800000)==0x7f800000]&=np.uint32(0xff7fffff)
    for row in raw.view(np.float32):yield 'finite_random',(*map(float,row),0.,0.)


def sqrt_bits(value):
    bits=struct.unpack('<I',struct.pack('<f',value))[0]
    if bits&0x7fffffff==0:return bits
    if bits&0x80000000 or bits>0x7f800000:return 0x7fc00000
    if bits==0x7f800000:return bits
    q=Fraction(float(value));n,d=q.numerator,q.denominator
    e=n.bit_length()-d.bit_length()
    if (n<(d<<e)) if e>=0 else ((n<<-e)<d):e-=1
    cut=e//2-23
    if cut>=0:d<<=2*cut
    else:n<<=-2*cut
    root=isqrt(n//d)
    if 4*n>d*(2*root+1)**2:root+=1
    return rounded_bits(Fraction(root)*(Fraction(2)**cut))


def sqrt_cases():
    for value in (0.,-0.,2.**-149,2.**-126-2.**-149,2.**-126,1.,4.,np.inf,-np.inf,np.nan,-1.):
        yield 'range_and_special',(value,0.,0.,0.)
    for exponent in range(-149,128):yield 'power',(2.**exponent,0.,0.,0.)
    rng=np.random.default_rng(991819)
    raw=rng.integers(1,0x7f800000,16384,dtype=np.uint32)
    for value in raw.view(np.float32):yield 'finite_random',(float(value),0.,0.,0.)


def product_bits(a,b):
    """Finite-physical helper semantics, including signed zero and invalid input."""
    ba,bb=(struct.unpack('<I',struct.pack('<f',v))[0] for v in (a,b))
    if (ba&0x7f800000)==0x7f800000 or (bb&0x7f800000)==0x7f800000:return 0x7fc00000
    if (ba&0x7fffffff)==0 or (bb&0x7fffffff)==0:return (ba^bb)&0x80000000
    return rounded_bits(Fraction(float(a))*Fraction(float(b)))


def product_cases():
    values=(0.,-0.,2.**-149,2.**-148,3*2.**-149,2.**-126-2.**-149,
            2.**-126,2.**-125,2.**-24,.5,1.,1+2.**-23,1.5,2.,2.**24,
            float(np.finfo(np.float32).max),np.inf,-np.inf,np.nan)
    for a in values:
        for b in values:
            for sign in (1,-1):yield 'range_tie_and_special',(sign*a,b,0.,0.)
    for exponent in range(-149,128):
        for factor in (.5,1.,1+2.**-23,1.5,2.):
            yield 'exponent_boundary',(2.**exponent,factor,0.,0.)
    rng=np.random.default_rng(20260914)
    raw=rng.integers(0,0xffffffff,(32768,2),dtype=np.uint32)
    raw[(raw&0x7f800000)==0x7f800000]&=np.uint32(0xff7fffff)
    for row in raw.view(np.float32):yield 'finite_random',(*map(float,row),0.,0.)


def sum_bits(a,b):
    ba,bb=(struct.unpack('<I',struct.pack('<f',v))[0] for v in (a,b))
    if (ba&0x7f800000)==0x7f800000 or (bb&0x7f800000)==0x7f800000:return 0x7fc00000
    if (ba&0x7fffffff)==0 and (bb&0x7fffffff)==0:return ba&bb&0x80000000
    return rounded_bits(Fraction(float(a))+Fraction(float(b)))


def addition_cases():
    def value(bits):return struct.unpack('<f',struct.pack('<I',bits))[0]
    raw_values=(0,1,2,3,0x3fffff,0x7ffffe,0x7fffff,0x800000,0x800001,
                0x1000000,0x3f000000,0x3f800000,0x3f800001,0x7f7fffff,
                0x7f800000,0x7fc00000)
    for a in raw_values:
        for b in raw_values:
            for signs in range(4):
                yield 'signed_range_and_special',(value(a|((signs&1)<<31)),value(b|((signs>>1)<<31)),0.,0.)
    for exponent in range(1,255):
        for mantissa in (0,1,2,0x3fffff,0x7ffffe,0x7fffff):
            a=(exponent<<23)|mantissa
            for delta in (-1,0,1):
                b=a+delta
                if b>=0x7f800000:continue
                for sign in (0,0x80000000):
                    yield 'cancellation',(value(a|sign),value(b|(sign^0x80000000)),0.,0.)
        # Both tie parities, each side of a halfway value, carry/borrow at
        # exponent boundaries, and exponent gaps beyond the machine word.
        for a in ((exponent<<23),(exponent<<23)|1,(exponent<<23)|0x7fffff):
            for gap in (1,3,4,23,24,25,31,32,100,254):
                small=max(1,exponent-gap)<<23 if exponent>gap else 1
                for delta in (-1,0,1):
                    for sign in (0,0x80000000):
                        yield 'alignment_rounding',(value(a),value((small+delta)|sign),0.,0.)
    rng=np.random.default_rng(20260916)
    raw=rng.integers(0,0xffffffff,(8192,2),dtype=np.uint32)
    for row in raw.view(np.float32):yield 'finite_random',(*map(float,row),0.,0.)


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--output', type=Path, required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--rk2', action='store_true', help='Exact .5*(state+stage+dt*rate), rounded once')
    mode.add_argument('--validity', action='store_true', help='Exact depth/momentum/foam admissibility')
    mode.add_argument('--divide', action='store_true', help='Correctly rounded represented FP32 division')
    mode.add_argument('--sqrt', action='store_true', help='Correctly rounded represented FP32 square root')
    mode.add_argument('--multiply', action='store_true', help='Exact finite represented FP32 product; nonfinite inputs invalid')
    mode.add_argument('--add', action='store_true', help='Exact finite represented FP32 sum; nonfinite inputs invalid')
    args = parser.parse_args(); manifest = args.output.with_suffix('.json')
    if args.output.exists() or manifest.exists(): raise FileExistsError(args.output)
    records = []; payload = bytearray()
    wide = args.rk2 or args.validity or args.divide or args.sqrt or args.multiply or args.add; stride = 20 if wide else 16
    for name, triple in (addition_cases() if args.add else product_cases() if args.multiply else sqrt_cases() if args.sqrt else division_cases() if args.divide else validity_cases() if args.validity else rk2_cases() if args.rk2 else cases()):
        represented = np.asarray(triple, dtype=np.float32)
        if args.add: expected=sum_bits(*represented[:2])
        elif args.multiply: expected=product_bits(*represented[:2])
        elif args.sqrt: expected=sqrt_bits(represented[0])
        elif args.divide: expected = divided_bits(*represented[:2])
        elif args.validity: expected = int(valid_state(represented))
        else:
            values = list(Fraction(float(v)) for v in represented)
            expected = rounded_bits((values[0]+values[1]+values[2]*values[3])/2 if args.rk2 else values[0]+values[1]*values[2])
        payload.extend(struct.pack('<ffffI' if wide else '<fffI', *represented, expected))
        if name != 'finite_random': records.append(dict(index=len(payload)//stride-1, name=name, expected_bits=expected))
    data = struct.pack('<III', 0x52534650, 10 if args.add else 8 if args.multiply else 6 if args.sqrt else 4 if args.divide else 3 if args.validity else 2 if args.rk2 else 1, len(payload)//stride)+payload
    with args.output.open('xb') as stream: stream.write(data)
    report = dict(scope=__doc__,count=len(payload)//stride,rk2=args.rk2,validity=args.validity,divide=args.divide,sqrt=args.sqrt,multiply=args.multiply,add=args.add,selected=records,
        fixture_sha256=hashlib.sha256(data).hexdigest(),implementation_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    with manifest.open('x') as stream: json.dump(report, stream, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
