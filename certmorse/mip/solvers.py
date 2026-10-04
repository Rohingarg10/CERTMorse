"""Integer formulation, implication CP-SAT emitter, identical MPS for HiGHS."""
from copy import deepcopy
from pathlib import Path
import math
import time
import numpy as np
from ortools.sat.python import cp_model
import highspy
from .milp import SolveResult
from ..complex import lower_star_gradient
from ..forman import witness, NegativeCycle
from .compression import compress_bounds


def _fallback(model, hint):
    if model.cell_lo is None:
        return None, None
    candidates = []
    if hint is not None and hint.get('y') is not None:
        candidates.append(np.asarray(hint['y'], dtype=np.int8))
    g = (model.cell_lo[:model.cx.nv].astype(float)+model.cell_hi[:model.cx.nv])/2
    a,b = lower_star_gradient(g, model.cx)
    candidates.append(np.concatenate((a,b)))
    best = (None,None)
    for y in candidates:
        a,b = model.cx.split_matching(y)
        x = witness(a,b,model.cell_lo,model.cell_hi,model.cx)
        if not isinstance(x, NegativeCycle) and (best[1] is None or y.sum() > best[1].sum()):
            best = (x,y)
    return best


def _extra_rows(model):
    # Valid torus Morse inequalities: at least one critical vertex and triangle.
    # These two redundant rows substantially improve the count proof on wide bands.
    nve = len(model.cx.pairs_ve)
    rows = [({p:1 for p in range(nve)},None,model.cx.nv-1),
            ({p:1 for p in range(nve,len(model.cx.pairs))},None,model.cx.nt-1)]
    if model.cell_lo is not None:
        for p,(face,coface) in enumerate(model.cx.pairs):
            if model.cell_lo[coface] > model.cell_hi[face]:
                rows.append(({p:1},0,0))
    for p,value in model.fixed_y.items():
        rows.append(({int(p):1}, int(value), int(value)))
    if model.target_matches is not None:
        rows.append(({p:1 for p in range(len(model.cx.pairs))}, model.target_matches, model.target_matches))
    rows.extend(model.cuts)
    return rows


def _cpsat(model, limit, threads, hint, log_path):
    cp = cp_model.CpModel()
    cx = model.cx
    y = [cp.new_bool_var(f'y_{p}') for p in range(len(cx.pairs))]
    x = []
    if model.formulation == 'A':
        x = [cp.new_int_var(int(lo),int(hi),f'x_{c}') for c,(lo,hi) in enumerate(zip(model.cell_lo,model.cell_hi))]
        for p,(s,t) in enumerate(cx.pairs):
            cp.add(x[t] <= x[s]).only_enforce_if(y[p])
            cp.add(x[s]+1 <= x[t]).only_enforce_if(y[p].Not())
    incident = [[] for _ in range(cx.nc)]
    for p,(s,t) in enumerate(cx.pairs):
        incident[s].append(y[p]); incident[t].append(y[p])
    for terms in incident:
        cp.add(sum(terms) <= 1)
    for terms,lo,hi in _extra_rows(model):
        expr = sum(int(c)*y[p] for p,c in terms.items())
        if lo is not None: cp.add(expr >= lo)
        if hi is not None: cp.add(expr <= hi)
    weights = np.ones(len(y),dtype=np.int64) if model.weights is None else model.weights
    cp.maximize(sum(int(w)*v for w,v in zip(weights,y)))
    if hint:
        for v,value in zip(y,hint.get('y',[])): cp.add_hint(v,int(value))
        for v,value in zip(x,hint.get('x',[])): cp.add_hint(v,int(value))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = limit
    solver.parameters.num_workers = threads
    solver.parameters.random_seed = int((hint or {}).get('seed',0))
    solver.parameters.relative_gap_limit = 0.0
    solver.parameters.stop_after_first_solution = model.first_feasible
    solver.parameters.log_search_progress = True
    solver.parameters.log_to_stdout = False
    Path(log_path).parent.mkdir(parents=True,exist_ok=True)
    with open(log_path,'w',encoding='utf8') as stream:
        solver.log_callback = lambda msg: stream.write(msg+'\n')
        status = solver.solve(cp)
    mapping = {cp_model.OPTIMAL:'OPTIMAL',cp_model.FEASIBLE:'FEASIBLE',cp_model.UNKNOWN:'NO_SOLUTION',cp_model.INFEASIBLE:'INFEASIBLE',cp_model.MODEL_INVALID:'ERROR'}
    yy = np.array([solver.value(v) for v in y],dtype=np.int8) if status in (cp_model.OPTIMAL,cp_model.FEASIBLE) else None
    return mapping[status], yy, solver.best_objective_bound, solver.num_branches


def emit_highs(model, *, global_big_m=False, compress=True, integer_potentials=False):
    h = highspy.Highs()
    h.setOptionValue('output_flag',False)
    cx = model.cx
    offset = cx.nc if model.formulation == 'A' else 0
    weights = np.ones(len(cx.pairs),dtype=np.int64) if model.weights is None else model.weights
    if offset:
        cell_lo,cell_hi = compress_bounds(model.cell_lo,model.cell_hi) if compress else (model.cell_lo,model.cell_hi)
        for c,(lo,hi) in enumerate(zip(cell_lo,cell_hi)):
            h.addCol(0,float(lo),float(hi),0,np.array([],dtype=np.int32),np.array([],dtype=float))
            # With integer bounds and binary y, the difference system is
            # integral (network matrix). Continuous x preserves exactly the
            # feasible y and avoids fragile mixed-integer cuts on potentials.
            if integer_potentials: h.changeColIntegrality(c,highspy.HighsVarType.kInteger)
            h.passColName(c,f'x_{c}')
    for p,w in enumerate(weights):
        c = offset+p
        h.addCol(float(w),0,1,0,np.array([],dtype=np.int32),np.array([],dtype=float))
        h.changeColIntegrality(c,highspy.HighsVarType.kInteger)
        h.passColName(c,f'y_{p}')
    def row(terms,lo,hi):
        ids = np.array(list(terms),dtype=np.int32)
        vals = np.array(list(terms.values()),dtype=float)
        h.addRow(-highspy.kHighsInf if lo is None else float(lo),highspy.kHighsInf if hi is None else float(hi),len(ids),ids,vals)
    if offset:
        big_m = int(cell_hi.max())-int(cell_lo.min())+1
        for p,(s,t) in enumerate(cx.pairs):
            # Bounds prove these per-incidence constants valid. A global M
            # is retained only for reproducing the historical counterexamples.
            matched_m = big_m if global_big_m else max(0,int(cell_hi[t])-int(cell_lo[s]))
            unmatched_m = big_m if global_big_m else max(0,int(cell_hi[s])-int(cell_lo[t])+1)
            row({int(t):1,int(s):-1,offset+p:matched_m},None,matched_m)
            row({int(s):1,int(t):-1,offset+p:-unmatched_m},None,-1)
    incident = [{} for _ in range(cx.nc)]
    for p,(s,t) in enumerate(cx.pairs):
        incident[s][offset+p]=1; incident[t][offset+p]=1
    for terms in incident: row(terms,None,1)
    for terms,lo,hi in _extra_rows(model): row({offset+p:c for p,c in terms.items()},lo,hi)
    h.changeObjectiveSense(highspy.ObjSense.kMaximize)
    return h


def _highs(model,limit,threads,hint,log_path):
    Path(log_path).parent.mkdir(parents=True,exist_ok=True)
    mps = str(Path(log_path).with_suffix('.mps'))
    if emit_highs(model).writeModel(mps) == highspy.HighsStatus.kError or not Path(mps).is_file():
        raise RuntimeError('HiGHS failed to export the model')
    h = highspy.Highs()
    h.setOptionValue('output_flag',True)
    h.setOptionValue('log_to_console',False)
    if h.readModel(mps) == highspy.HighsStatus.kError:
        raise RuntimeError('HiGHS failed to read the exported model')
    for option,value in [('time_limit',limit),('threads',threads),('mip_rel_gap',0.),('mip_abs_gap',0.),('mip_feasibility_tolerance',1e-9),('primal_feasibility_tolerance',1e-9),('dual_feasibility_tolerance',1e-9),('presolve','on'),('log_file',str(log_path))]:
        if h.setOptionValue(option,value) != highspy.HighsStatus.kOk:
            raise RuntimeError(f'HiGHS rejected option {option}={value}')
    if hint is not None and hint.get('y') is not None:
        offset = model.cx.nc if model.formulation == 'A' else 0
        if offset and hint.get('x') is not None:
            ids = np.arange(offset+len(model.cx.pairs),dtype=np.int32)
            lo,hi = compress_bounds(model.cell_lo,model.cell_hi)
            a,b = model.cx.split_matching(hint['y'])
            compressed_x = witness(a,b,lo,hi,model.cx)
            if isinstance(compressed_x,NegativeCycle):
                raise ValueError('infeasible HiGHS hint')
            values = np.concatenate((compressed_x,hint['y'])).astype(float)
        else:
            ids = np.arange(offset,offset+len(model.cx.pairs),dtype=np.int32)
            values = np.asarray(hint['y'],dtype=float)
        if h.setSolution(len(ids),ids,values) != highspy.HighsStatus.kOk:
            raise RuntimeError('HiGHS rejected the MIP start')
    if h.run() == highspy.HighsStatus.kError:
        return 'ERROR',None,float('nan'),None
    status, info, solution = h.getModelStatus(),h.getInfo(),h.getSolution()
    if status == highspy.HighsModelStatus.kOptimal: canonical='OPTIMAL'
    elif status == highspy.HighsModelStatus.kInfeasible: canonical='INFEASIBLE'
    elif solution.value_valid and info.primal_solution_status == 2: canonical='FEASIBLE'
    elif status == highspy.HighsModelStatus.kTimeLimit: canonical='NO_SOLUTION'
    else: canonical='ERROR'
    offset = model.cx.nc if model.formulation=='A' else 0
    yy = np.rint(solution.col_value[offset:]).astype(np.int8) if canonical in ('OPTIMAL','FEASIBLE') else None
    return canonical,yy,info.mip_dual_bound,info.mip_node_count


def solve(model,backend,time_limit_s,threads,hint,log_path):
    start = time.perf_counter()
    status,yy,bound,nodes = {'cpsat':_cpsat,'highs':_highs}[backend](model,time_limit_s,threads,hint,log_path)
    # Raise numerical bounds just below an integer before applying floor.
    # Raw solver values remain in the log; HiGHS is never a certificate.
    if backend=='highs' and math.isfinite(bound) and 0 <= math.ceil(bound)-bound <= 1e-7:
        bound=float(math.ceil(bound))
    xx = None
    if yy is not None and model.cell_lo is not None:
        a,b = model.cx.split_matching(yy)
        try: xx = witness(a,b,model.cell_lo,model.cell_hi,model.cx)
        except ValueError: xx = NegativeCycle([],[],[], 'invalid matching')
        if isinstance(xx,NegativeCycle): status,xx,yy='NUMERIC_INVALID',None,None
    # Never substitute a fallback into a fixed-y feasibility probe or sampling solve.
    if status not in ('NUMERIC_INVALID','ERROR','INFEASIBLE') and not model.fixed_y and model.target_matches is None:
        fallback_x,fallback_y = _fallback(model,hint)
        if fallback_y is not None and (yy is None or fallback_y.sum() > yy.sum()): xx,yy=fallback_x,fallback_y
    incumbent = model.cx.nc-2*int(yy.sum()) if yy is not None else None
    if model.weights is None and yy is not None and math.isfinite(bound) and int(yy.sum()) > bound+1e-7:
        # A verified feasible count above a backend's claimed upper bound
        # invalidates that numerical result, even if its matching was feasible.
        return SolveResult('NUMERIC_INVALID',None,None,None,False,bound,None,time.perf_counter()-start,nodes,None,None)
    count_bound = model.cx.nc-2*math.floor(bound) if model.weights is None and math.isfinite(bound) else None
    objective = int(yy.sum()) if yy is not None else None
    gap = max(0.,(bound-objective)/max(1,abs(bound))) if model.weights is None and objective is not None and math.isfinite(bound) else None
    return SolveResult(status,incumbent,count_bound,incumbent if status=='OPTIMAL' and model.weights is None else None,backend=='cpsat' and count_bound is not None and status not in ('ERROR','NUMERIC_INVALID','INFEASIBLE'),bound,gap,time.perf_counter()-start,nodes,xx,yy)


def sample_optima(model,kappa_star,max_optima,time_cap_s,rng,*,initial_result=None,log_path='results/stage1/sampling.log'):
    if initial_result is not None and (initial_result.status != 'OPTIMAL' or initial_result.kappa_opt != kappa_star):
        raise ValueError('multiplicity sampling requires a proven initial optimum')
    sampled = deepcopy(model)
    sampled.target_matches = (model.cx.nc-kappa_star)//2
    sampled.first_feasible = True
    deadline = time.perf_counter()+time_cap_s
    results=[] if initial_result is None else [initial_result]
    def exclude(ve):
        terms = {p:(-1 if value else 1) for p,value in enumerate(ve)}
        sampled.cuts.append((terms,1-int(ve.sum()),None))
    if initial_result is not None: exclude(initial_result.y[:len(model.cx.pairs_ve)])
    while len(results)<max_optima and time.perf_counter()<deadline:
        sampled.weights = np.concatenate((rng.integers(0,1001,len(model.cx.pairs_ve)),np.zeros(len(model.cx.pairs_et),dtype=np.int64)))
        sample_log = str(Path(log_path).with_name(Path(log_path).stem+f'-{len(results):02d}.log'))
        result = solve(sampled,'cpsat',max(.01,deadline-time.perf_counter()),8,None,sample_log)
        if result.status=='INFEASIBLE': return results,'exhausted'
        if result.y is None: break
        results.append(result)
        ve = result.y[:len(model.cx.pairs_ve)]
        # Hamming distance from this vertex-edge matching >= 1.
        exclude(ve)
    return results,'complete' if len(results)==max_optima else 'time_capped'
