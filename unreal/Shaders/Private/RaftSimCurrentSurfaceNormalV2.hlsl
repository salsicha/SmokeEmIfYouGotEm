// Isolated shading-only ripple candidate. No WPO or physical fluid state.
// Analytic derivatives of compact kernels on a triangular lattice avoid the
// zero-gradient square-grid lines of the V1 quintic value-noise experiment.
float2 p = RiverUV * 3.0 - FlowDisplacement.xy;
float2 slope = 0.0;
static const float2 directions[8] = {
    float2(1,0), float2(0.707106781,0.707106781), float2(0,1),
    float2(-0.707106781,0.707106781), float2(-1,0),
    float2(-0.707106781,-0.707106781), float2(0,-1),
    float2(0.707106781,-0.707106781)
};
[unroll] for (int band = 0; band < 3; ++band)
{
    float frequency = band == 0 ? 2.8 : (band == 1 ? 6.1 : 13.7);
    float amplitude = band == 0 ? 0.022 : (band == 1 ? 0.016 : 0.007);
    float2 axis = band == 0 ? float2(0.8, 0.6) :
        (band == 1 ? float2(-0.6, 0.8) : float2(0.384615385, -0.923076923));
    float2 q = float2(dot(axis,p), dot(float2(-axis.y,axis.x),p)) * frequency
        + float2(17.73,-9.31) * band;
    float2 cell = floor(q + (q.x + q.y) * 0.366025404);
    float2 x0 = q - cell + (cell.x + cell.y) * 0.211324865;
    float2 middle = x0.x > x0.y ? float2(1,0) : float2(0,1);
    float2 gradient = 0.0;
    [unroll] for (int corner = 0; corner < 3; ++corner)
    {
        float2 offset = corner == 0 ? float2(0,0) : (corner == 1 ? middle : float2(1,1));
        float2 x = x0 - offset + float(corner) * 0.211324865;
        uint2 i = asuint(int2(cell + offset));
        uint h = (i.x * 1597334677u) ^ (i.y * 3812015801u);
        h ^= h >> 16u;
        h *= 2246822519u;
        h ^= h >> 13u;
        float2 g = directions[h & 7u];
        float t = max(0.5 - dot(x,x), 0.0);
        float t3 = t*t*t;
        // d/dx [ t^4 dot(g,x) ]; the kernel and its derivatives vanish
        // at its support boundary, including between neighbouring triangles.
        gradient += 70.0 * (t*t3*g - 8.0*t3*x*dot(g,x));
    }
    float footprint = max(length(ddx(q)), length(ddy(q)));
    float visible = 1.0 - smoothstep(0.12,0.60,footprint);
    slope += float2(axis.x*gradient.x-axis.y*gradient.y,
                    axis.y*gradient.x+axis.x*gradient.y) * amplitude * visible;
}
return normalize(float3(-slope * max(Strength,0.0), 1.0));
