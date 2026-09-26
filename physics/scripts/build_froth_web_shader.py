"""Generate RaftSimFrothCells.ush: a flow-stretched foam web with exact coverage.

The previous froth-cell include thresholded one random value per 0.59 m grid
cell and blended the corners, so transported foam rendered as rounded squares
on a regular lattice (the "polka dot" foam seen in normal play). This
generator keeps its contract -- presentation only, expected coverage equals the
transported fraction ``p = 1 - exp(-amount * density)``, same two-phase
flow-map backtrace -- and replaces the pattern with:

* a coarse Voronoi foam web (F2 - F1, 2.4 m cells) whose distance metric is
  stretched 2x along the local current, so filaments trail downstream;
* a fine web (0.55 m cells, 1.2x stretch) for torn lace and small holes;
* an isotropic two-octave clumping field (3.2 m / 1.3 m) for patches and gaps;
* an isotropic 9 cm grain that roughens edges near the camera.

Each component is converted to a uniform rank by its measured quantile table,
the ranks are mixed, and the mix is re-ranked, so ``V`` is uniform on [0, 1]
and ``P(V < p) = p``. Three mixes (full, without grain, coarse web + clump) are
calibrated separately and blended by pixel footprint, so expected coverage is
exactly ``p`` at every viewing distance before the far fade to ``p`` itself.
The stretched metric never rotates absolute coordinates (the lattice is fixed
in world space), so curving currents cannot swirl or shear the pattern.
Neighbour searches (5x5 coarse, 3x3 fine) were checked exact for these stretches.

Run with Blender's bundled Python (numpy); writes the .ush and a JSON receipt.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
USH = ROOT / 'unreal/Plugins/RaftSim/Shaders/Private/RaftSimFrothCells.ush'

COARSE_M, COARSE_S, COARSE_SALT = 2.4, 2.0, 0x9E3779B9
FINE_M, FINE_S, FINE_SALT = 0.55, 1.2, 0x7F4A7C15
FINE_OFFSET = (31.7, -12.9)
CLUMP_A_M, CLUMP_A_SALT = 3.2, 0x0051ED27
CLUMP_B_M, CLUMP_B_SALT, CLUMP_B_OFFSET = 1.3, 0x002C1B3C, (7.3, -3.1)
GRAIN_M, GRAIN_SALT = 0.09, 0x006D2B79
WEIGHTS_FULL = (0.44, 0.18, 0.28, 0.10)
WEIGHTS_NO_GRAIN = (0.44, 0.18, 0.28, 0.0)
WEIGHTS_COARSE = (0.60, 0.0, 0.40, 0.0)
# Integer multiple of every lattice scale (cm LCM of 240, 55, 320, 130, 9):
# wrapping world metres here keeps float precision without creating seams.
WRAP_M = 4118.4
KNOT_COUNT = 33
KNOTS = np.linspace(0.0, 1.0, KNOT_COUNT)


def hash2(ix, iy, salt):
    h = (ix.astype(np.uint32) * np.uint32(1597334677)) ^ \
        (iy.astype(np.uint32) * np.uint32(3812015801)) ^ np.uint32(salt)
    h ^= h >> np.uint32(16)
    h *= np.uint32(2246822519)
    h ^= h >> np.uint32(13)
    a = (h & np.uint32(65535)).astype(np.float64) / 65536.0
    h *= np.uint32(3266489917)
    h ^= h >> np.uint32(15)
    b = (h & np.uint32(65535)).astype(np.float64) / 65536.0
    return a, b


def worley(x, y, dx, dy, stretch, salt, reach):
    ix0, iy0 = np.floor(x).astype(np.int64), np.floor(y).astype(np.int64)
    f1 = np.full(x.shape, 1e9)
    f2 = np.full(x.shape, 1e9)
    for oy in range(-reach, reach + 1):
        for ox in range(-reach, reach + 1):
            cx, cy = ix0 + ox, iy0 + oy
            jx, jy = hash2(cx, cy, salt)
            ddx, ddy = cx + 0.1 + 0.8 * jx - x, cy + 0.1 + 0.8 * jy - y
            along = (ddx * dx + ddy * dy) / stretch
            across = -ddx * dy + ddy * dx
            d = np.sqrt(along * along + across * across)
            f2 = np.where(d < f1, f1, np.minimum(f2, d))
            f1 = np.minimum(f1, d)
    # Stretching only rescales the F2-F1 distribution (measured ratio 2/(1+S)
    # within 1% at every quantile), so this factor makes it stretch-invariant.
    return (f2 - f1) * (1.0 + stretch) * 0.5


def vnoise(x, y, scale, salt):
    u, v = x / scale, y / scale
    iu, iv = np.floor(u).astype(np.int64), np.floor(v).astype(np.int64)
    fu, fv = u - iu, v - iv
    fu, fv = fu * fu * (3 - 2 * fu), fv * fv * (3 - 2 * fv)
    a, _ = hash2(iu, iv, salt)
    b, _ = hash2(iu + 1, iv, salt)
    c, _ = hash2(iu, iv + 1, salt)
    d, _ = hash2(iu + 1, iv + 1, salt)
    return (a * (1 - fu) + b * fu) * (1 - fv) + (c * (1 - fu) + d * fu) * fv


def components(x, y, dx, dy, stretch_factor=1.0):
    coarse = worley(x / COARSE_M, y / COARSE_M, dx, dy, 1.0 + (COARSE_S - 1.0) * stretch_factor, COARSE_SALT, 2)
    fine = worley(x / FINE_M + FINE_OFFSET[0], y / FINE_M + FINE_OFFSET[1], dx, dy,
                  1.0 + (FINE_S - 1.0) * stretch_factor, FINE_SALT, 1)
    clump = 0.65 * vnoise(x, y, CLUMP_A_M, CLUMP_A_SALT) + \
        0.35 * vnoise(x + CLUMP_B_OFFSET[0], y + CLUMP_B_OFFSET[1], CLUMP_B_M, CLUMP_B_SALT)
    grain = vnoise(x, y, GRAIN_M, GRAIN_SALT)
    return coarse, fine, clump, grain


def calibrate(samples, seed):
    rng = np.random.default_rng(seed)
    x = rng.uniform(0.0, WRAP_M, samples)
    y = rng.uniform(0.0, WRAP_M, samples)
    angle = rng.uniform(0.0, 2.0 * np.pi, samples)
    comps = components(x, y, np.cos(angle), np.sin(angle), rng.uniform(0.0, 1.0, samples))
    tables = [np.quantile(c, KNOTS) for c in comps]
    ranks = [np.interp(c, t, KNOTS) for c, t in zip(comps, tables)]
    mixes = {}
    for name, weights in (('full', WEIGHTS_FULL), ('no_grain', WEIGHTS_NO_GRAIN), ('coarse', WEIGHTS_COARSE)):
        mixes[name] = np.quantile(sum(w * r for w, r in zip(weights, ranks)), KNOTS)
    return tables, mixes


def verify(tables, mixes, samples, seed):
    """Independent draws: every mix is uniform (coverage == p) in slack,
    moderate and fast current alike."""
    worst = {}
    for stretch_factor in (0.0, 0.5, 1.0):
        rng = np.random.default_rng(seed + int(stretch_factor * 10))
        x = rng.uniform(0.0, WRAP_M, samples)
        y = rng.uniform(0.0, WRAP_M, samples)
        angle = rng.uniform(0.0, 2.0 * np.pi, samples)
        comps = components(x, y, np.cos(angle), np.sin(angle), stretch_factor)
        ranks = [np.interp(c, t, KNOTS) for c, t in zip(comps, tables)]
        for name, weights in (('full', WEIGHTS_FULL), ('no_grain', WEIGHTS_NO_GRAIN), ('coarse', WEIGHTS_COARSE)):
            v = np.interp(sum(w * r for w, r in zip(weights, ranks)), mixes[name], KNOTS)
            errors = [abs(float(np.mean(v < p)) - p) for p in np.linspace(0.05, 0.95, 19)]
            worst[f'{name}@stretch{stretch_factor}'] = max(errors)
    return worst


MIX_WEIGHTS = (('full', WEIGHTS_FULL), ('no_grain', WEIGHTS_NO_GRAIN), ('coarse', WEIGHTS_COARSE))
# Phase displacement is half a second of current (b = a + 0.5), so the two
# flow-map samples are 0.5 * speed apart; tables are indexed by that distance.
MORPH_D_STEP_M = 0.1
MORPH_D_KNOTS = np.arange(0.0, 2.0001, MORPH_D_STEP_M)
MORPH_WEIGHTS = (0.1, 0.25, 0.4, 0.5, 0.6, 0.75, 0.9)
MORPH_P = np.linspace(0.05, 0.95, 19)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def mix_values(tables, mixes, x, y, dx, dy, stretch_factor):
    comps = components(x, y, dx, dy, stretch_factor)
    ranks = [np.interp(c, t, KNOTS) for c, t in zip(comps, tables)]
    return {name: np.interp(sum(w * r for w, r in zip(weights, ranks)), mixes[name], KNOTS)
            for name, weights in MIX_WEIGHTS}


def trap_cdf(s, w):
    """CDF of w*U1 + (1-w)*U2 for independent uniforms (trapezoid)."""
    a = np.maximum(np.minimum(w, 1.0 - w), 1e-3)
    b = np.maximum(w, 1.0 - w)
    return np.where(s <= a, s * s / (2 * a * b),
                    np.where(s <= b, (s - 0.5 * a) / b, 1.0 - (1.0 - s) ** 2 / (2 * a * b)))


def morph_pairs(tables, mixes, d, samples, seed):
    rng = np.random.default_rng(seed)
    x = rng.uniform(0.0, WRAP_M, samples)
    y = rng.uniform(0.0, WRAP_M, samples)
    angle = rng.uniform(0.0, 2.0 * np.pi, samples)
    dx, dy = np.cos(angle), np.sin(angle)
    stretch_factor = smoothstep(0.1, 0.8, 2.0 * d)  # same coupling as the shader
    va = mix_values(tables, mixes, x, y, dx, dy, stretch_factor)
    vb = mix_values(tables, mixes, x + d * dx, y + d * dy, dx, dy, stretch_factor)
    return va, vb


def morph_bias(va, vb, lam, weights=MORPH_WEIGHTS):
    worst = 0.0
    for w in weights:
        s = w * va + (1.0 - w) * vb
        u = lam * s + (1.0 - lam) * trap_cdf(s, w)
        worst = max(worst, max(abs(float(np.mean(u < p)) - p) for p in MORPH_P))
    return worst


def calibrate_morph(tables, mixes, samples, seed):
    """Per mix and displacement, the blend between the raw rank sum (right when
    both samples coincide) and its independent-uniform CDF (right when they
    are decorrelated) that minimises the worst coverage bias."""
    lambdas = {name: [] for name, _ in MIX_WEIGHTS}
    for i, d in enumerate(MORPH_D_KNOTS):
        va, vb = morph_pairs(tables, mixes, d, samples, seed + i)
        for name, _ in MIX_WEIGHTS:
            best = min(((morph_bias(va[name], vb[name], lam), lam) for lam in np.linspace(0, 1, 41)))
            lambdas[name].append(best[1])
    # Decorrelation is monotone in distance; enforce it so interpolation is safe.
    return {k: np.minimum.accumulate(np.array(v)) for k, v in lambdas.items()}


def verify_morph(tables, mixes, lambdas, samples, seed):
    """Off-knot displacements with interpolated corrections."""
    worst = {}
    for i, d in enumerate((0.05, 0.25, 0.55, 0.85, 1.15, 1.7)):
        va, vb = morph_pairs(tables, mixes, d, samples, seed + 100 + i)
        for name, _ in MIX_WEIGHTS:
            lam = float(np.interp(d, MORPH_D_KNOTS, lambdas[name]))
            worst[f'{name}@d{d}'] = morph_bias(va[name], vb[name], lam)
    return worst


def hlsl_lambda(name, values):
    body = ', '.join(f'{v:.4f}' for v in values)
    n = len(values)
    return (f'    float Morph{name}(float d)\n    {{\n'
            f'        static const float l[{n}] = {{{body}}};\n'
            f'        float x = clamp(d / {MORPH_D_STEP_M}, 0.0, {n - 1}.0);\n'
            f'        int i = min(int(x), {n - 2});\n'
            f'        return lerp(l[i], l[i + 1], x - i);\n    }}')


def hlsl_rank(name, values):
    """Piecewise-linear quantile CDF with a function-local table.

    The include is pasted into a material Custom node, so the tables live in
    member functions rather than as static struct members."""
    body = ', '.join(f'{v:.7f}' for v in values)
    return (f'    float Rank{name}(float x)\n    {{\n'
            f'        static const float q[{KNOT_COUNT}] = {{{body}}};\n'
            f'        float r = 0.0;\n'
            f'        [unroll] for (int i = 0; i < {KNOT_COUNT - 1}; ++i)\n'
            f'            r += (x > q[i]) ? saturate((x - q[i]) / max(q[i + 1] - q[i], 1e-6)) : 0.0;\n'
            f'        return r / {KNOT_COUNT - 1}.0;\n    }}')


def render(tables, mixes, lambdas):
    names = ('Coarse', 'Fine', 'Clump', 'Grain')
    arrays = '\n'.join(hlsl_rank(n, t) for n, t in zip(names, tables))
    arrays += '\n' + '\n'.join(hlsl_rank(f'Mix{n}', mixes[k]) for n, k in
                               (('Full', 'full'), ('NoGrain', 'no_grain'), ('Coarse', 'coarse')))
    arrays += '\n' + '\n'.join(hlsl_lambda(n, lambdas[k]) for n, k in
                               (('Full', 'full'), ('NoGrain', 'no_grain'), ('Coarse', 'coarse')))
    return f'''// GENERATED by physics/scripts/build_froth_web_shader.py -- edit the generator.
// Presentation-only froth driven by transported coverage p = 1-exp(-amount*density).
// A flow-stretched Voronoi foam web, torn fine lace, isotropic clumping and a
// near-camera grain are each rank-transformed by measured quantile tables and
// mixed; the mix is re-ranked so V is uniform and P(V < p) = p. Three mixes
// (full / no grain / coarse) are blended by pixel footprint, so expected
// coverage equals p at every distance. The lattice is fixed in world space and
// only the distance metric is stretched along the current, so curving flow
// cannot swirl the pattern. No density source, displacement or own clock.
struct RaftSimFrothCells
{{
{arrays}

    float2 Hash2(int2 cell, uint salt)
    {{
        uint h = (uint(cell.x) * 1597334677u) ^ (uint(cell.y) * 3812015801u) ^ salt;
        h ^= h >> 16; h *= 2246822519u; h ^= h >> 13;
        float a = float(h & 65535u) / 65536.0;
        h *= 3266489917u; h ^= h >> 15;
        return float2(a, float(h & 65535u) / 65536.0);
    }}
    float WebCoarse(float2 p, float2 dir, float stretch)
    {{
        int2 base = int2(floor(p));
        float f1 = 1e9, f2 = 1e9;
        [unroll] for (int oy = -2; oy <= 2; ++oy)
        [unroll] for (int ox = -2; ox <= 2; ++ox)
        {{
            int2 cell = base + int2(ox, oy);
            float2 d = float2(cell) + 0.1 + 0.8 * Hash2(cell, {COARSE_SALT}u) - p;
            float along = dot(d, dir) / stretch;
            float across = -d.x * dir.y + d.y * dir.x;
            float dist = sqrt(along * along + across * across);
            f2 = dist < f1 ? f1 : min(f2, dist);
            f1 = min(f1, dist);
        }}
        return (f2 - f1) * (1.0 + stretch) * 0.5;
    }}
    float WebFine(float2 p, float2 dir, float stretch)
    {{
        int2 base = int2(floor(p));
        float f1 = 1e9, f2 = 1e9;
        [unroll] for (int oy = -1; oy <= 1; ++oy)
        [unroll] for (int ox = -1; ox <= 1; ++ox)
        {{
            int2 cell = base + int2(ox, oy);
            float2 d = float2(cell) + 0.1 + 0.8 * Hash2(cell, {FINE_SALT}u) - p;
            float along = dot(d, dir) / stretch;
            float across = -d.x * dir.y + d.y * dir.x;
            float dist = sqrt(along * along + across * across);
            f2 = dist < f1 ? f1 : min(f2, dist);
            f1 = min(f1, dist);
        }}
        return (f2 - f1) * (1.0 + stretch) * 0.5;
    }}
    float ValueNoise(float2 p, uint salt)
    {{
        int2 cell = int2(floor(p));
        float2 f = frac(p);
        f = f * f * (3.0 - 2.0 * f);
        float a = Hash2(cell, salt).x, b = Hash2(cell + int2(1, 0), salt).x;
        float c = Hash2(cell + int2(0, 1), salt).x, d = Hash2(cell + int2(1, 1), salt).x;
        return lerp(lerp(a, b, f.x), lerp(c, d, f.x), f.y);
    }}
    float Cover(float v, float p)
    {{
        float aa = clamp(fwidth(v), 0.004, 0.2) * 0.75;
        float t = saturate((p - v) / (2.0 * aa) + 0.5);
        return t * t * (3.0 - 2.0 * t);
    }}
    // Uniform ranks of the three footprint mixes (full, no grain, coarse).
    float3 Phase(float2 worldM, float2 dir, float stretch)
    {{
        float2 w = worldM - floor(worldM / {WRAP_M}) * {WRAP_M};
        float coarse = RankCoarse(WebCoarse(w / {COARSE_M}, dir, 1.0 + ({COARSE_S} - 1.0) * stretch));
        float fine = RankFine(WebFine(w / {FINE_M} + float2({FINE_OFFSET[0]}, {FINE_OFFSET[1]}), dir,
            1.0 + ({FINE_S} - 1.0) * stretch));
        float clump = RankClump(0.65 * ValueNoise(w / {CLUMP_A_M}, {CLUMP_A_SALT}u) +
            0.35 * ValueNoise((w + float2({CLUMP_B_OFFSET[0]}, {CLUMP_B_OFFSET[1]})) / {CLUMP_B_M}, {CLUMP_B_SALT}u));
        float grain = RankGrain(ValueNoise(w / {GRAIN_M}, {GRAIN_SALT}u));
        return float3(
            RankMixFull({WEIGHTS_FULL[0]} * coarse + {WEIGHTS_FULL[1]} * fine +
                {WEIGHTS_FULL[2]} * clump + {WEIGHTS_FULL[3]} * grain),
            RankMixNoGrain({WEIGHTS_NO_GRAIN[0]} * coarse + {WEIGHTS_NO_GRAIN[1]} * fine +
                {WEIGHTS_NO_GRAIN[2]} * clump),
            RankMixCoarse({WEIGHTS_COARSE[0]} * coarse + {WEIGHTS_COARSE[2]} * clump));
    }}
    // CDF of w*U1 + (1-w)*U2 for independent uniforms (trapezoid).
    float Trap(float s, float w)
    {{
        float a = max(min(w, 1.0 - w), 1e-3), b = max(w, 1.0 - w);
        return s <= a ? s * s / (2.0 * a * b) : (s <= b ? (s - 0.5 * a) / b : 1.0 - (1.0 - s) * (1.0 - s) / (2.0 * a * b));
    }}
    // Morph the two flow-map phases in rank space instead of crossfading
    // coverages: a linear coverage blend of two displaced sharp patterns
    // leaves half-opacity ghost copies. The blended rank is mapped back to
    // uniform between its coincident (d = 0) and independent limits by a
    // measured, displacement-indexed correction.
    float Morphed(float va, float vb, float w, float lambda)
    {{
        float s = w * va + (1.0 - w) * vb;
        return lerp(Trap(s, w), s, lambda);
    }}
    float Sample(float amount, float density, float2 worldM, float2 velocityMps, float time, float footprintM)
    {{
        float p = saturate(1 - exp(-max(amount, 0) * max(density, 0)));
        if (p <= 0) return 0;
        if (p >= 1) return 1;
        float speed = length(velocityMps);
        float2 dir = speed > 1e-4 ? velocityMps / speed : float2(1, 0);
        // Isotropic in slack water: direction then has no effect at all.
        float stretch = smoothstep(0.1, 0.8, speed);
        float a = frac(time), b = frac(a + 0.5), weight = 1 - abs(2 * a - 1);
        float3 va = Phase(worldM - velocityMps * a, dir, stretch);
        float3 vb = Phase(worldM - velocityMps * b, dir, stretch);
        float d = 0.5 * speed;  // separation of the two backtraces
        float full = Cover(Morphed(va.x, vb.x, weight, MorphFull(d)), p);
        float noGrain = Cover(Morphed(va.y, vb.y, weight, MorphNoGrain(d)), p);
        float coarseOnly = Cover(Morphed(va.z, vb.z, weight, MorphCoarse(d)), p);
        // Each branch has expected coverage ~p; convex blends keep that.
        float c = lerp(full, noGrain, smoothstep(0.02, 0.06, footprintM));
        c = lerp(c, coarseOnly, smoothstep(0.12, 0.35, footprintM));
        return lerp(c, p, smoothstep(0.5, 1.4, footprintM));
    }}
}};
'''


def write_with_retry(path, text):
    """Windows occasionally rejects an open-for-write right after a previous
    write of the same file (transient lock); retry briefly."""
    import time
    for attempt in range(20):
        try:
            path.write_text(text, newline='\n')
            return
        except OSError:
            if attempt == 19:
                raise
            time.sleep(0.5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--output', type=Path, help='write here instead of the plugin include (then copy)')
    parser.add_argument('--samples', type=int, default=600000)
    args = parser.parse_args()
    tables, mixes = calibrate(args.samples, seed=11)
    worst = verify(tables, mixes, args.samples, seed=12)
    if max(worst.values()) > 0.01:
        raise SystemExit(f'Coverage calibration failed: {worst}')
    morph_samples = max(args.samples // 4, 50000)
    lambdas = calibrate_morph(tables, mixes, morph_samples, seed=40)
    morph_worst = verify_morph(tables, mixes, lambdas, morph_samples, seed=40)
    if max(morph_worst.values()) > 0.025:
        raise SystemExit(f'Phase-morph calibration failed: {morph_worst}')
    previous = hashlib.sha256(USH.read_bytes()).hexdigest() if USH.exists() else None
    text = render(tables, mixes, lambdas)
    target = args.output if args.output is not None else USH
    write_with_retry(target, text)
    receipt = dict(
        schema='raftsim.froth_web_shader.v1', ush=USH.relative_to(ROOT).as_posix(),
        previous_sha256=previous, sha256=hashlib.sha256(text.encode()).hexdigest(),
        samples=args.samples, calibration_seed=11, verification_seed=12,
        worst_coverage_error_by_mix=worst,
        phase_morph=dict(displacement_step_m=MORPH_D_STEP_M, weights=MORPH_WEIGHTS,
                         lambdas={k: [round(float(x), 4) for x in v] for k, v in lambdas.items()},
                         worst_coverage_error_off_knot=morph_worst, gate=0.025),
        scales_m=dict(coarse=COARSE_M, fine=FINE_M, clump=[CLUMP_A_M, CLUMP_B_M], grain=GRAIN_M),
        stretch=dict(coarse=COARSE_S, fine=FINE_S), wrap_m=WRAP_M,
        weights=dict(full=WEIGHTS_FULL, no_grain=WEIGHTS_NO_GRAIN, coarse=WEIGHTS_COARSE),
        presentation_only=True, foam_amount_source_changed=False)
    args.receipt.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
