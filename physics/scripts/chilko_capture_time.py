"""Decode the retained 2023 LAS capture times without guessing from filenames.

LAS 1.4 global-encoding bit 0 selects standard GPS time minus 1e9 seconds.
GPS was 18 seconds ahead of UTC throughout 2023. This deliberately refuses
other years and GPS-week encoding rather than assuming a leap-second table.
References: ASPRS LAS 1.4 R15; USNO GPS Timing Data and Information.
"""
from datetime import datetime, timezone

import numpy as np


def utc_seconds_2023(adjusted_gps, global_encoding):
    values = np.asarray(adjusted_gps, dtype=float)
    if (not isinstance(global_encoding, (int, np.integer)) or global_encoding < 0 or
            not global_encoding & 1):
        raise ValueError('Adjusted standard GPS encoding required; no guessed GPS week')
    if values.ndim != 1 or not len(values) or not np.isfinite(values).all():
        raise ValueError('Finite nonempty point timestamps required')
    seconds = values + 1_000_000_000. + 315_964_800. - 18.
    if np.any(seconds < 1_672_531_200.) or np.any(seconds >= 1_704_067_200.):
        raise ValueError('Only verified 2023 GPS-to-UTC offset supported')
    return seconds


def date_counts(seconds, utc_offset_hours=0):
    """Report UTC and fixed-PST alternatives; neither assigns a gauge timezone."""
    values = np.asarray(seconds, dtype=float)
    if (values.ndim != 1 or not len(values) or not np.isfinite(values).all() or
            utc_offset_hours not in (0, -8)):
        raise ValueError('Finite timestamps and explicit UTC or fixed PST required')
    days = np.floor((values + utc_offset_hours*3600.)/86400.).astype(np.int64)
    unique, counts = np.unique(days, return_counts=True)
    return {datetime.fromtimestamp(int(day)*86400, timezone.utc).date().isoformat(): int(count)
            for day, count in zip(unique, counts)}
