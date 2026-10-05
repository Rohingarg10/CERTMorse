"""Measured persistence references, never substituted for a solver proof."""
import numpy as np
from ..persistence import persistence, lower_star_values

ZERO_SCALE = 10**6  # v1.8.2 section 3; fixed independently of the diagnostic band.
ZERO_HALF_WIDTH_UNITS = 500  # v1.8.2 section 3.
TIME_LIMIT_S = 600  # v1.6 section 6.4.
THREADS = 8  # v1.6 section 6.4.


def truth_count(field,cx,scale,log_path):
    from ..landscape import field_diagnostics
    from ..complex import lower_star_gradient
    from ..scaling import model_band,cell_band
    from ..forman import witness,NegativeCycle
    from .model_A import build_A
    from .solvers import solve
    diagnostics=field_diagnostics(field,cx,scale)
    a,b=lower_star_gradient(field,cx)
    count=cx.nc-2*int(a.sum()+b.sum())
    if diagnostics['ties_exact']==0:
        assert count==2*(diagnostics['strict_minima']+diagnostics['strict_maxima'])
        return dict(**diagnostics,kappa_true=count,kappa_zero=None,kappa_zero_scale=None)
    eta=ZERO_HALF_WIDTH_UNITS/ZERO_SCALE
    lo,hi=cell_band(*model_band(np.asarray(field)-eta,np.asarray(field)+eta,ZERO_SCALE),cx)
    x=witness(a,b,lo,hi,cx)
    assert not isinstance(x,NegativeCycle)
    result=solve(build_A(lo,hi,cx),'cpsat',TIME_LIMIT_S,THREADS,
                 dict(x=x,y=np.concatenate((a,b))),log_path)
    assert result.status=='OPTIMAL', 'kappa_zero requires a proven optimum'
    return dict(**diagnostics,kappa_true=None,kappa_zero=result.kappa_opt,kappa_zero_scale=ZERO_SCALE)


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
