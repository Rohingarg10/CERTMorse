"""Simulation-only basin resolution check, v1.8.3 sections 1 and 2."""
from functools import lru_cache
import numpy as np
from scipy.optimize import minimize
from .complex import TorusComplex,lower_star_gradient,basins
from .grid import grid_point,grid_coords,GAMMA_PERIOD
from .instances import independent_landscape
from .landscape import BETA_PERIODS,COMMON_BETA_PERIOD,exact_points
from .metrics import BASIN_TOLERANCE

RESOLUTION_XATOL = 1e-9  # v1.8.3 section 2.
RESOLUTION_FATOL = 1e-12  # v1.8.3 section 2.
INFORMATIVE_LIMIT = 0.95  # v1.8.3 section 1.
GRID_SIZES = (16,24,32,48)  # v1.8.3 section 2.
RESOLUTION_INSTANCES = ('E8a','E8b','W8a','W8b','R8a')  # v1.8.3 section 2.


def resolution_check(inst,field,channel,seed,*,common_domain=False):
    field=np.asarray(field,dtype=float)
    if field.ndim!=2 or field.shape[0]!=field.shape[1]:
        raise ValueError('square shot-free grid required')
    cx=TorusComplex(field.shape[0]);flat=field.ravel()
    period=COMMON_BETA_PERIOD if common_domain else BETA_PERIODS[channel]
    ve,_=lower_star_gradient(field,cx);labels=basins(ve,cx);roots=np.unique(labels)
    grid_depths=[];continuous_depths=[];refinements=[]
    @lru_cache(maxsize=None)
    def value(gamma,beta):
        gamma=gamma%GAMMA_PERIOD;beta=beta%BETA_PERIODS[channel]
        if channel in ('a','d','d0'):
            return independent_landscape(inst,gamma,beta,channel)
        return float(exact_points(inst,[(gamma,beta)],channel,seed)[0][0])
    for root in roots:
        vertices=np.flatnonzero(labels==root)
        deepest=int(vertices[np.argmin(flat[vertices])])
        start=np.array(grid_point(deepest%cx.m,deepest//cx.m,cx.m,period))
        best=[value(*map(float,start)),start.copy()]
        stopped=[False]
        def inside(point):
            # D11 assigns equal area to each vertex. Its grid cell is the
            # half-open nearest-vertex cell; wrap both integer indices.
            i,j=grid_coords(*point,cx.m,period)
            v=int(np.floor(i+0.5))%cx.m+cx.m*(int(np.floor(j+0.5))%cx.m)
            return labels[v]==root
        def objective(point):
            result=value(*map(float,point))
            if inside(point) and result<best[0]: best[:]=[result,point.copy()]
            return result
        def callback(point):
            if not inside(point):
                stopped[0]=True
                raise StopIteration
        result=minimize(objective,start,method='Nelder-Mead',callback=callback,
                        options=dict(xatol=RESOLUTION_XATOL,fatol=RESOLUTION_FATOL))
        grid_depths.append(float(flat[deepest]));continuous_depths.append(float(best[0]))
        refinements.append(dict(root=int(root),deepest_vertex=deepest,
                                point=list(map(float,best[1])),converged=bool(result.success),
                                stopped_at_boundary=stopped[0],evaluations=int(result.nfev)))
    grid_depths=np.array(grid_depths);continuous_depths=np.array(continuous_depths)
    tau=BASIN_TOLERANCE*inst.W
    grid_global=grid_depths<=grid_depths.min()+tau
    continuous_global=continuous_depths<=continuous_depths.min()+tau
    adequate=bool(np.array_equal(grid_global,continuous_global))
    P0_grid=float(np.mean(np.isin(labels,roots[grid_global])))
    P0_cont=float(np.mean(np.isin(labels,roots[continuous_global])))
    return dict(resolution_adequate=adequate,
                worst_grid_depth_error=float(np.max(grid_depths-continuous_depths)),
                P0_grid=P0_grid,P0_cont=P0_cont,
                RQ2_informative=adequate and P0_grid<=INFORMATIVE_LIMIT,
                resolution_cell_rule='half-open nearest-vertex cells (equal D11 areas)',
                grid_depths=grid_depths.tolist(),continuous_depths=continuous_depths.tolist(),
                grid_global=grid_global.tolist(),continuous_global=continuous_global.tolist(),
                refinements=refinements)
