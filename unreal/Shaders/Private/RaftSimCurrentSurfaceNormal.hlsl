// Custom-material body for the isolated survey normal review.
// RiverUV is station/lateral divided by 3 m; the current integral is in metres.
// This is shading detail, NOT displacement, a fluid solve, or raft support.
// Quintic value-noise derivatives give compact, C2-continuous ripples without
// mirrored image borders or indefinitely long sinusoidal crests.
float2 p = RiverUV * 3.0 - FlowDisplacement.xy;
float2 slope = float2(0.0, 0.0);
[unroll] for (int band = 0; band < 3; ++band)
{
    float frequency = band == 0 ? 0.62 : (band == 1 ? 1.43 : 3.19);
    float amplitude = band == 0 ? 0.22 : (band == 1 ? 0.13 : 0.065);
    float2 axis = band == 0 ? float2(0.8, 0.6) :
        (band == 1 ? float2(-0.6, 0.8) : float2(0.384615385, -0.923076923));
    float2 q = float2(dot(axis, p), dot(float2(-axis.y, axis.x), p)) * frequency;
    q += float2(17.73, -9.31) * band;
    float2 cell = floor(q);
    float2 t = frac(q);
    float2 s = t*t*t * (t * (t * 6.0 - 15.0) + 10.0);
    float2 ds = 30.0 * t*t * (t - 1.0) * (t - 1.0);
    // Integer hashes avoid sin() precision/implementation differences at
    // distant stations. Negative lattice cells are intentionally wrapped.
    uint2 i = asuint(int2(cell));
    uint4 h = uint4(i.x, i.x + 1u, i.x, i.x + 1u) * 1597334677u
        ^ uint4(i.y, i.y, i.y + 1u, i.y + 1u) * 3812015801u;
    h ^= h >> 16u;
    h *= 2246822519u;
    h ^= h >> 13u;
    float4 n = float4(h & 0x00ffffffu) / 16777215.0;
    float2 gradient = float2(
        lerp(n.y - n.x, n.w - n.z, s.y) * ds.x,
        lerp(n.z - n.x, n.w - n.y, s.x) * ds.y);
    // Filter subpixel bands before they become grazing-angle glitter. The
    // filter changes shading only and has no independent animation clock.
    float footprint = max(length(ddx(q)), length(ddy(q)));
    float visible = 1.0 - smoothstep(0.20, 0.85, footprint);
    // R transpose transforms the sampled gradient back into river space.
    slope += float2(axis.x * gradient.x - axis.y * gradient.y,
                    axis.y * gradient.x + axis.x * gradient.y) * amplitude * visible;
}
return normalize(float3(-slope * max(Strength, 0.0), 1.0));
