import numpy as np
from .milp import MilpModel


def build_A(cell_lo, cell_hi, cx):
    lo, hi = np.asarray(cell_lo, dtype=np.int64), np.asarray(cell_hi, dtype=np.int64)
    if lo.shape != (cx.nc,) or hi.shape != (cx.nc,) or np.any(lo > hi):
        raise ValueError('nonempty cell bands required')
    return MilpModel(cx, lo.copy(), hi.copy())
