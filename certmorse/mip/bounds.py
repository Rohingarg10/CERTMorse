"""Measured persistence references, never substituted for a solver proof."""
import numpy as np
from ..persistence import persistence, lower_star_values


def persistence_count(diagram, delta):
    finite = sum(int(np.sum(np.isfinite(d[:,1]) & ((d[:,1]-d[:,0]) >= 2*delta))) for d in diagram.values())
    essential = sum(int(np.sum(np.isinf(d[:,1]))) for d in diagram.values())
    if essential != 4:
        raise ValueError('expected four essential torus classes')
    return 4+2*finite


def persistence_bounds(midpoint, lower, upper, cx):
    diagram = persistence(lower_star_values(midpoint,cx),cx,1)
    widths = (np.asarray(upper)-np.asarray(lower))/2
    return dict(UB_pers=persistence_count(diagram,float(widths.min())),
                LB_pers=persistence_count(diagram,float(widths.max())))
