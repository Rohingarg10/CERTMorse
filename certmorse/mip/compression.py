"""Exact domain compression for 0/1 difference constraints, not scalar data."""
import numpy as np


def compress_bounds(lo, hi):
    """Preserve feasible matchings while capping empty endpoint gaps at n.

    A simple path on n cells contains at most n-1 strict inequalities.
    Feasibility requires hi[u]-lo[v] >= the strict length of every path
    u -> v. Compression preserves every endpoint comparison to lengths
    <= n; cycles are independent of bounds. Returned coordinates are only
    for the numerical backend. Reconstruct witnesses in original units.
    """
    lo, hi = np.asarray(lo), np.asarray(hi)
    endpoints = sorted(set(map(int, lo)) | set(map(int, hi)))
    coords = {endpoints[0]: 0}
    for previous, current in zip(endpoints, endpoints[1:]):
        coords[current] = coords[previous] + min(current-previous, len(lo))
    return (np.array([coords[int(v)] for v in lo], dtype=np.int64),
            np.array([coords[int(v)] for v in hi], dtype=np.int64))
