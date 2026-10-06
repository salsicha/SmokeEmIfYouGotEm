"""Transverse Mercator and Web Mercator conversions on the WGS84 ellipsoid (numpy only).

Snyder series, sub-millimetre within a few degrees of the central meridian:
enough to register open data (IGN CRTM05, UTM, EPSG:3857 tiles, OSM lon/lat)
in one metric frame. CR05 / CRTM05 (EPSG:5367) is realised on WGS84 at the
metre level; datum shifts below that are ignored.
"""
import numpy as np

A, F = 6378137.0, 1 / 298.257223563
E2 = F * (2 - F)
EP2 = E2 / (1 - E2)

CRTM05 = dict(lon0=-84.0, k0=0.9999, fe=500000.0, fn=0.0)


def utm(zone, south=False):
    return dict(lon0=-183.0 + 6.0 * zone, k0=0.9996, fe=500000.0, fn=10000000.0 if south else 0.0)


def _m(lat):
    return A * ((1 - E2 / 4 - 3 * E2 ** 2 / 64 - 5 * E2 ** 3 / 256) * lat
                - (3 * E2 / 8 + 3 * E2 ** 2 / 32 + 45 * E2 ** 3 / 1024) * np.sin(2 * lat)
                + (15 * E2 ** 2 / 256 + 45 * E2 ** 3 / 1024) * np.sin(4 * lat)
                - (35 * E2 ** 3 / 3072) * np.sin(6 * lat))


def tm_forward(lon_deg, lat_deg, p):
    lon, lat = np.radians(lon_deg), np.radians(lat_deg)
    n = A / np.sqrt(1 - E2 * np.sin(lat) ** 2)
    t = np.tan(lat) ** 2
    c = EP2 * np.cos(lat) ** 2
    aa = np.cos(lat) * (lon - np.radians(p['lon0']))
    k0 = p['k0']
    x = k0 * n * (aa + (1 - t + c) * aa ** 3 / 6 + (5 - 18 * t + t * t + 72 * c - 58 * EP2) * aa ** 5 / 120) + p['fe']
    y = k0 * (_m(lat) + n * np.tan(lat) * (aa * aa / 2 + (5 - t + 9 * c + 4 * c * c) * aa ** 4 / 24
                                            + (61 - 58 * t + t * t + 600 * c - 330 * EP2) * aa ** 6 / 720)) + p['fn']
    return x, y


def tm_inverse(x, y, p):
    k0 = p['k0']
    m = (np.asarray(y, float) - p['fn']) / k0
    mu = m / (A * (1 - E2 / 4 - 3 * E2 ** 2 / 64 - 5 * E2 ** 3 / 256))
    e1 = (1 - np.sqrt(1 - E2)) / (1 + np.sqrt(1 - E2))
    phi1 = (mu + (3 * e1 / 2 - 27 * e1 ** 3 / 32) * np.sin(2 * mu)
            + (21 * e1 ** 2 / 16 - 55 * e1 ** 4 / 32) * np.sin(4 * mu)
            + (151 * e1 ** 3 / 96) * np.sin(6 * mu) + (1097 * e1 ** 4 / 512) * np.sin(8 * mu))
    s, c_, t_ = np.sin(phi1), np.cos(phi1), np.tan(phi1)
    n1 = A / np.sqrt(1 - E2 * s * s)
    t1 = t_ * t_
    c1 = EP2 * c_ * c_
    r1 = A * (1 - E2) / (1 - E2 * s * s) ** 1.5
    d = (np.asarray(x, float) - p['fe']) / (n1 * k0)
    lat = phi1 - (n1 * t_ / r1) * (d ** 2 / 2 - (5 + 3 * t1 + 10 * c1 - 4 * c1 ** 2 - 9 * EP2) * d ** 4 / 24
                                   + (61 + 90 * t1 + 298 * c1 + 45 * t1 ** 2 - 252 * EP2 - 3 * c1 ** 2) * d ** 6 / 720)
    lon = np.radians(p['lon0']) + (d - (1 + 2 * t1 + c1) * d ** 3 / 6
                                   + (5 - 2 * c1 + 28 * t1 - 3 * c1 ** 2 + 8 * EP2 + 24 * t1 ** 2) * d ** 5 / 120) / c_
    return np.degrees(lon), np.degrees(lat)


def lonlat_to_merc(lon_deg, lat_deg):
    return np.radians(lon_deg) * A, A * np.log(np.tan(np.pi / 4 + np.radians(lat_deg) / 2))


def merc_to_lonlat(x, y):
    return np.degrees(np.asarray(x, float) / A), np.degrees(2 * np.arctan(np.exp(np.asarray(y, float) / A)) - np.pi / 2)
