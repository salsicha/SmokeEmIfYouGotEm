"""Conservative availability events for a frozen directed transfer network.

This integrates a specified constant-capacity fluid network, NOT the nonlinear
shallow-water equations. Positive reservoirs discharge at their original rate;
empty reservoirs pass only supplied inflow, in the original outlet proportions.
All times, volumes and edge integrals are rational arithmetic on the supplied
float data. Zero volume is an event identity, never a depth threshold or repair.
"""
from fractions import Fraction as F
import math


def solve_exact(matrix, rhs):
    rows = [list(row)+[value] for row, value in zip(matrix, rhs)]
    count = len(rows)
    for col in range(count):
        pivot = next((i for i in range(col, count) if rows[i][col]), None)
        if pivot is None:
            raise ValueError('Singular supplied empty-reservoir routing system')
        rows[col], rows[pivot] = rows[pivot], rows[col]
        for i in range(col+1, count):
            if not rows[i][col]:
                continue
            ratio = rows[i][col]/rows[col][col]
            for j in range(col+1, count+1):
                rows[i][j] -= ratio*rows[col][j]
            rows[i][col] = F(0)
    answer = [F(0)]*count
    for i in reversed(range(count)):
        answer[i] = (rows[i][-1]-sum((rows[i][j]*answer[j] for j in range(i+1, count)), F(0)))/rows[i][i]
    return answer


def routing(volume, edges, outgoing):
    count = len(volume)
    supplied = {i for i, v in enumerate(volume) if v > 0}
    while True:
        reached = supplied | {b for a, b, _ in edges if a in supplied}
        if reached == supplied:
            break
        supplied = reached
    # Unsupplied zero cycles cannot circulate imaginary water.
    factors = [F(int(i in supplied)) for i in range(count)]
    free = set()
    for _ in range(count+1):
        incoming = [F(0)]*count
        for a, b, rate in edges:
            incoming[b] += rate*factors[a]
        violated = {i for i in supplied if volume[i] == 0 and incoming[i] < outgoing[i]*factors[i]}
        if not violated:
            return factors
        if violated.issubset(free):
            raise ValueError('Exact empty-reservoir routing failed its balance')
        free.update(violated)
        ordered = sorted(free)
        positions = {node: i for i, node in enumerate(ordered)}
        matrix = [[F(0) for _ in ordered] for _ in ordered]
        rhs = [F(0)]*len(ordered)
        for i, node in enumerate(ordered):
            matrix[i][i] = outgoing[node]
        for a, b, rate in edges:
            if b not in free:
                continue
            row = positions[b]
            if a in free:
                matrix[row][positions[a]] -= rate
            else:
                rhs[row] += rate*factors[a]
        values = solve_exact(matrix, rhs)
        for node, value in zip(ordered, values):
            if not 0 <= value <= factors[node]:
                raise ValueError('Empty routing must only reduce unavailable outflow')
            factors[node] = value
    raise ValueError('Empty-reservoir policy exceeded finite node count')


def integrate(volumes, transfers, duration):
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError('Positive finite requested interval required')
    original = [v if isinstance(v, F) else F(float(v)) for v in volumes]
    if not original or any(v < 0 for v in original) or sum(original) <= 0:
        raise ValueError('Nonnegative original volumes with positive total required')
    count = len(original)
    pairs = {}
    for a, b, rate in transfers:
        if not 0 <= a < count or not 0 <= b < count or a == b or not math.isfinite(rate) or rate <= 0:
            raise ValueError('Positive directed transfer between distinct original nodes required')
        pairs[a, b] = pairs.get((a, b), F(0))+F(float(rate))
    edges = [(a, b, rate) for (a, b), rate in sorted(pairs.items())]
    outgoing = [F(0)]*count
    for a, _, rate in edges:
        outgoing[a] += rate
    volume, exposure = list(original), [F(0)]*count
    integrals = [F(0)]*len(edges)
    time, finish = F(0), F(float(duration))
    events = []
    for _ in range(count+1):
        factors = routing(volume, edges, outgoing)
        rates = [rate*factors[a] for a, _, rate in edges]
        net = [F(0)]*count
        for (a, b, _), rate in zip(edges, rates):
            net[a] -= rate
            net[b] += rate
        candidates = [(v/-r, i) for i, (v, r) in enumerate(zip(volume, net)) if v > 0 and r < 0]
        remaining = finish-time
        span = min([remaining]+[t for t, _ in candidates])
        if span <= 0:
            raise ValueError('Nonpositive event interval; no timestep repair')
        for i in range(count):
            exposure[i] += span*(volume[i]+net[i]*span/2)
            volume[i] += span*net[i]
            if volume[i] < 0 or exposure[i] < 0:
                raise ValueError('Exact event produced negative water or exposure')
        for i, rate in enumerate(rates):
            integrals[i] += rate*span
        time += span
        dried = [i for t, i in candidates if t == span]
        if dried:
            if any(volume[i] != 0 for i in dried):
                raise ValueError('Drying event must exhaust its exact ledger')
            events.append(dict(time=time, regions=dried))
        if time == finish:
            break
    else:
        raise ValueError('Frozen network exceeded finite drainage-event count')
    incoming, spent = [F(0)]*count, [F(0)]*count
    for (a, b, _), transfer in zip(edges, integrals):
        spent[a] += transfer
        incoming[b] += transfer
    if any(v != old+inc-out for v, old, inc, out in zip(volume, original, incoming, spent)):
        raise ValueError('Exact incident mass ledger failed')
    return dict(volume=volume, exposure=exposure, events=events,
        transfers=[(a, b, value) for (a, b, _), value in zip(edges, integrals) if value > 0],
        incoming=incoming, outgoing=spent, capacity=outgoing, original=original, duration=finish)
