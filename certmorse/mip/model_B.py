import time
import math
from pathlib import Path
from .milp import MilpModel
from .solvers import solve, _fallback
from ..forman import witness, NegativeCycle
from .cuts import all_cycle_pairs, band_cycles, cycle_cut, band_cut

CUT_LIMIT = 200  # A.4


def build_B(cx):
    return MilpModel(cx, formulation='B')


def solve_B_lazy(cx,cell_lo,cell_hi,backend,time_limit_s,threads,hint,log_path,*,cut_callback=None):
    model = build_B(cx)
    # Pre-separate the one-pair band cycles: a matched pair is impossible when
    # its coface's lower bound exceeds its face's upper bound. These are the
    # same signed Benders cuts as a source--face--coface negative cycle.
    for p,(face,coface) in enumerate(cx.pairs):
        if cell_lo[coface] > cell_hi[face]:
            cut=({p:-1},0,None)
            model.cuts.append(cut)
            if cut_callback: cut_callback('band',cut,None)
    initial_cuts=len(model.cuts)
    def signature(cut):
        terms,lo,hi=cut
        return tuple(sorted(terms.items())),lo,hi
    seen={signature(cut) for cut in model.cuts}
    def add(cut,family,y):
        key=signature(cut)
        if key in seen: return False
        seen.add(key);model.cuts.append(cut)
        if cut_callback: cut_callback(family,cut,y.copy())
        return True
    start = time.perf_counter()
    deadline = start+time_limit_s
    Path(log_path).parent.mkdir(parents=True,exist_ok=True)
    Path(log_path).write_text('',encoding='utf8')
    result = None
    best_bound=cx.nc/2
    iterations=0
    for iteration in range(CUT_LIMIT):
        remaining = deadline-time.perf_counter()
        if remaining <= 0: break
        iteration_path=Path(log_path).with_name(Path(log_path).stem+f'-iter-{iteration:03d}.log')
        result = solve(model,backend,remaining,threads,hint,str(iteration_path))
        iterations=iteration+1
        if math.isfinite(result.bound): best_bound=min(best_bound,result.bound)
        if iteration_path.exists():
            with open(log_path,'a',encoding='utf8') as combined:
                combined.write(iteration_path.read_text(encoding='utf8'))
        if result.y is None: break
        cycles = all_cycle_pairs(result.y,cx)
        if cycles:
            if not any([add(cycle_cut(cycle),'cycle',result.y) for cycle in cycles]):
                raise RuntimeError('cycle separator made no progress')
            continue
        a,b = cx.split_matching(result.y)
        x = witness(a,b,cell_lo,cell_hi,cx)
        if not isinstance(x,NegativeCycle):
            result.x = x
            result.wall_s = time.perf_counter()-start
            result.cut_iters = iteration
            result.cuts_added=len(model.cuts)-initial_cuts
            return result
        if not any([add(band_cut(conflict),'band',result.y) for conflict in band_cycles(result.y,cell_lo,cell_hi,cx)]):
            raise RuntimeError('band separator made no progress')
    fallback = MilpModel(cx,cell_lo,cell_hi)
    xx,yy = _fallback(fallback,hint)
    if result is None:
        from .milp import SolveResult
        # Matching-only bound |K|/2 is valid without a solve.
        result=SolveResult('NO_SOLUTION',None,0,None,backend=='cpsat',cx.nc/2,None,0,None,None,None)
    result.x,result.y=xx,yy
    result.kappa_incumbent=cx.nc-2*int(yy.sum()) if yy is not None else None
    result.kappa_opt=None
    result.bound=best_bound
    result.kappa_lb=cx.nc-2*math.floor(best_bound)
    if result.status not in ('ERROR','NUMERIC_INVALID','INFEASIBLE'):
        result.status='CUT_LIMIT' if iterations==CUT_LIMIT else ('FEASIBLE' if yy is not None else 'NO_SOLUTION')
    result.gap=max(0.,(result.bound-int(yy.sum()))/max(1,abs(result.bound))) if yy is not None and math.isfinite(result.bound) else None
    result.cut_iters=iterations
    result.cuts_added=len(model.cuts)-initial_cuts
    result.wall_s=time.perf_counter()-start
    return result
