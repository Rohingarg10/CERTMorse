"""Matching-dependent measurements; their locations and basins are predictions."""
import numpy as np
from .complex import basins


def critical_counts(y, cx):
    used=np.bincount(cx.pairs[np.asarray(y,dtype=bool)].ravel(),minlength=cx.nc)>0
    return tuple(int(np.sum(~used[cx.dim==q])) for q in (0,1,2))


def basin_probability(y, mean, W, cx):
    ve,_=cx.split_matching(y)
    labels=basins(ve,cx)
    critical=np.unique(labels)
    field=np.asarray(mean).reshape(-1)
    selected=critical[field[critical]<=field[critical].min()+.02*W]
    return float(np.mean(np.isin(labels,selected)))
