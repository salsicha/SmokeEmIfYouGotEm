"""Numpy transverse Mercator (Snyder 1987 series) for GRS80/WGS84 grids.

Covers the projected frames of the Colorado/Hance sources without pyproj:
UTM zones and US State Plane transverse Mercator zones (for example Arizona
Central, NAD83(2011): lat0 31, lon0 -111.9166667, k0 0.9999, false easting
213360 m). Accuracy of the series is millimetres within a zone. NAD83(2011)
and WGS84 differ by about a metre horizontally; callers that mix them must
say so.
"""
import numpy as np

A = 6378137.0
F_GRS80 = 1 / 298.257222101
F_WGS84 = 1 / 298.257223563


def _consts(f):
    e2 = f * (2 - f)
    return e2, e2 / (1 - e2)


def _meridian(lat, e2):
    return A * ((1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256) * lat
                - (3 * e2 / 8 + 3 * e2 ** 2 / 32 + 45 * e2 ** 3 / 1024) * np.sin(2 * lat)
                + (15 * e2 ** 2 / 256 + 45 * e2 ** 3 / 1024) * np.sin(4 * lat)
                - (35 * e2 ** 3 / 3072) * np.sin(6 * lat))


def tm_forward(lon_deg, lat_deg, lon0_deg, lat0_deg=0.0, k0=0.9996, fe=500000.0, fn=0.0, f=F_GRS80):
    e2, ep2 = _consts(f)
    lat = np.radians(lat_deg); lon = np.radians(lon_deg); lon0 = np.radians(lon0_deg)
    n = A / np.sqrt(1 - e2 * np.sin(lat) ** 2)
    t = np.tan(lat) ** 2
    c = ep2 * np.cos(lat) ** 2
    aa = np.cos(lat) * (lon - lon0)
    m = _meridian(lat, e2); m0 = _meridian(np.radians(lat0_deg), e2)
    x = k0 * n * (aa + (1 - t + c) * aa ** 3 / 6 + (5 - 18 * t + t * t + 72 * c - 58 * ep2) * aa ** 5 / 120)
    y = k0 * (m - m0 + n * np.tan(lat) * (aa * aa / 2 + (5 - t + 9 * c + 4 * c * c) * aa ** 4 / 24
                                          + (61 - 58 * t + t * t + 600 * c - 330 * ep2) * aa ** 6 / 720))
    return x + fe, y + fn


def tm_inverse(x, y, lon0_deg, lat0_deg=0.0, k0=0.9996, fe=500000.0, fn=0.0, f=F_GRS80):
    e2, ep2 = _consts(f)
    m = _meridian(np.radians(lat0_deg), e2) + (np.asarray(y, float) - fn) / k0
    mu = m / (A * (1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256))
    e1 = (1 - np.sqrt(1 - e2)) / (1 + np.sqrt(1 - e2))
    phi1 = (mu + (3 * e1 / 2 - 27 * e1 ** 3 / 32) * np.sin(2 * mu)
            + (21 * e1 ** 2 / 16 - 55 * e1 ** 4 / 32) * np.sin(4 * mu)
            + (151 * e1 ** 3 / 96) * np.sin(6 * mu) + (1097 * e1 ** 4 / 512) * np.sin(8 * mu))
    s, c0, t0 = np.sin(phi1), np.cos(phi1), np.tan(phi1)
    n1 = A / np.sqrt(1 - e2 * s * s)
    t1 = t0 * t0
    c1 = ep2 * c0 * c0
    r1 = A * (1 - e2) / (1 - e2 * s * s) ** 1.5
    d = (np.asarray(x, float) - fe) / (n1 * k0)
    lat = phi1 - (n1 * t0 / r1) * (d ** 2 / 2 - (5 + 3 * t1 + 10 * c1 - 4 * c1 ** 2 - 9 * ep2) * d ** 4 / 24
                                   + (61 + 90 * t1 + 298 * c1 + 45 * t1 ** 2 - 252 * ep2 - 3 * c1 ** 2) * d ** 6 / 720)
    lon = np.radians(lon0_deg) + (d - (1 + 2 * t1 + c1) * d ** 3 / 6
                                  + (5 - 2 * c1 + 28 * t1 - 3 * c1 ** 2 + 8 * ep2 + 24 * t1 ** 2) * d ** 5 / 120) / c0
    return np.degrees(lon), np.degrees(lat)


AZ_CENTRAL = dict(lon0_deg=-111.91666666666667, lat0_deg=31.0, k0=0.9999, fe=213360.0, fn=0.0)
UTM12 = dict(lon0_deg=-111.0, lat0_deg=0.0, k0=0.9996, fe=500000.0, fn=0.0)


def self_test():
    lon, lat = np.array([-111.93, -112.1]), np.array([36.046, 36.2])
    for p in (AZ_CENTRAL, UTM12):
        x, y = tm_forward(lon, lat, **p)
        lo, la = tm_inverse(x, y, **p)
        assert np.max(np.abs(lo - lon)) < 1e-8 and np.max(np.abs(la - lat)) < 1e-8
    return True


if __name__ == '__main__':
    print('round trip ok', self_test())
