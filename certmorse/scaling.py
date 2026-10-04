"""Reported-band scaling and outward certificate margin (§6.4)."""
import numpy as np

MIN_WIDTH_UNITS = 1000  # §6.4
MAX_SCALE = 10**7  # §6.4
CERT_MARGIN_UNITS = 14  # §6.4


def choose_scale(lower, upper):
    lower, upper = np.asarray(lower), np.asarray(upper)
    if lower.shape != upper.shape or not np.all(np.isfinite(lower)) or not np.all(np.isfinite(upper)):
        raise ValueError("finite equal-shaped bands required")
    widths = upper-lower
    if np.any(widths < 0):
        raise ValueError("empty interval")
    scale = 1
    while scale < MAX_SCALE and scale*widths.min() < MIN_WIDTH_UNITS:
        scale *= 10
    return scale, int(np.count_nonzero(widths*scale < MIN_WIDTH_UNITS))


def model_band(lower, upper, scale):
    lo, hi = np.asarray(lower, dtype=float).copy(), np.asarray(upper, dtype=float).copy()
    mid = (lo+hi)/2
    width = np.maximum(hi-lo, MIN_WIDTH_UNITS/scale)
    lo, hi = mid-width/2, mid+width/2
    return (np.ceil(lo*scale-CERT_MARGIN_UNITS).astype(np.int64),
            np.floor(hi*scale+CERT_MARGIN_UNITS).astype(np.int64))


def cell_band(vlo_int, vhi_int, cx):
    lo, hi = np.asarray(vlo_int).reshape(-1), np.asarray(vhi_int).reshape(-1)
    if lo.shape != (cx.nv,) or hi.shape != (cx.nv,) or np.any(lo > hi):
        raise ValueError("nonempty bounds for every vertex required")
    return (np.array([lo[list(vs)].max() for vs in cx.vertices], dtype=np.int64),
            np.array([hi[list(vs)].max() for vs in cx.vertices], dtype=np.int64))
