"""Matching-dependent measurements; their locations and basins are predictions."""
import numpy as np
from .complex import basins

BASIN_TOLERANCE = 0.02  # v1.8 section 4.5, amended by v1.8.2 section 2.


def critical_counts(y, cx):
    used=np.bincount(cx.pairs[np.asarray(y,dtype=bool)].ravel(),minlength=cx.nc)>0
    return tuple(int(np.sum(~used[cx.dim==q])) for q in (0,1,2))


def basin_probability(y, mean, W, cx, lower, upper):
    """Return depth P and tolerant P_possible in the reported, unscaled band."""
    ve,_=cx.split_matching(y)
    labels=basins(ve,cx)
    critical=np.unique(labels)
    field=np.asarray(mean).reshape(-1)
    lo=np.asarray(lower).reshape(-1);hi=np.asarray(upper).reshape(-1)
    assert field.shape==lo.shape==hi.shape==(cx.nv,), 'one band/depth value per vertex required'
    assert np.all(np.isfinite(field)) and np.all(np.isfinite(lo)) and np.all(np.isfinite(hi))
    assert np.all((lo<=field)&(field<=hi)), 'depth field lies outside the reported band'
    depths=np.array([field[labels==root].min() for root in critical])
    lower_depths=np.array([lo[labels==root].min() for root in critical])
    tau=BASIN_TOLERANCE*W
    selected=critical[depths<=depths.min()+tau]
    possible=critical[lower_depths<=hi.min()+tau]
    P=float(np.mean(np.isin(labels,selected)))
    P_possible=float(np.mean(np.isin(labels,possible)))
    assert P<=P_possible
    return P,P_possible
