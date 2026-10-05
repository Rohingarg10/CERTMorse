"""Reproduce historical disagreements and audit the exported integer model."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import highspy
import numpy as np
from certmorse.complex import TorusComplex,lower_star_gradient
from certmorse.forman import witness
from certmorse.mip import build_A,solve
from certmorse.mip.solvers import emit_highs


def audit(h,values):
    lp=h.getLp()
    violations=[]
    for c,value in enumerate(values):
        if not lp.col_lower_[c]<=value<=lp.col_upper_[c]: violations.append(['bound',c])
        if lp.integrality_[c]==highspy.HighsVarType.kInteger and value!=int(value): violations.append(['integrality',c])
    for row in range(lp.num_row_):
        _,indices,coefficients=h.getRowEntries(row)
        # Python integers, so coefficient cancellation is not a numerical test.
        activity=sum(int(a)*int(values[i]) for i,a in zip(indices,coefficients))
        if activity<lp.row_lower_[row] or activity>lp.row_upper_[row]: violations.append(['row',row,activity])
    objective=sum(int(c)*int(v) for c,v in zip(lp.col_cost_,values))
    return dict(violations=violations,objective=objective,maximize=lp.sense_==highspy.ObjSense.kMaximize)


def run(seeds,global_big_m=False,legacy=False):
    reports=[]
    output=Path('results/corrections/highs-diagnostics')/('legacy' if legacy else 'corrected');output.mkdir(parents=True,exist_ok=True)
    for m,seed in seeds:
        rng=np.random.default_rng(seed);cx=TorusComplex(m)
        g=rng.normal(size=cx.nv);width=rng.uniform(.01,.5,size=cx.nv)
        from certmorse.scaling import choose_scale,model_band,cell_band
        scale,_=choose_scale(g-width,g+width)
        lo,hi=cell_band(*model_band(g-width,g+width,scale),cx)
        model=build_A(lo,hi,cx)
        cp=solve(model,'cpsat',60,8,None,str(output/f'{m}-{seed}-cp.log'))
        assert cp.status=='OPTIMAL'
        a,b=lower_star_gradient(g,cx);y=np.concatenate((a,b));x=witness(a,b,lo,hi,cx)
        values=np.concatenate((cp.x,cp.y))
        if not legacy:
            from certmorse.mip.compression import compress_bounds
            clo,chi=compress_bounds(lo,hi)
            ca,cb=cx.split_matching(cp.y)
            values=np.concatenate((witness(ca,cb,clo,chi,cx),cp.y))
            x=witness(a,b,clo,chi,cx)
        for mode in ['direct','mps']:
            for presolve in ['on','off']:
                for hint in ['none','midpoint','cp']:
                    h=emit_highs(model,global_big_m=global_big_m,compress=not legacy,integer_potentials=legacy)
                    if mode=='mps':
                        path=output/f'{m}-{seed}.mps';h.writeModel(str(path))
                        h=highspy.Highs();h.setOptionValue('output_flag',False);h.readModel(str(path))
                    check=audit(h,values)
                    assert not check['violations'] and check['maximize']
                    for key,value in [('threads',8),('presolve',presolve),('mip_feasibility_tolerance',1e-9),('primal_feasibility_tolerance',1e-9),('dual_feasibility_tolerance',1e-9),('mip_rel_gap',0.),('mip_abs_gap',0.),('time_limit',10.)]:
                        assert h.setOptionValue(key,value)==highspy.HighsStatus.kOk
                    if hint!='none':
                        start=np.concatenate((x,y)) if hint=='midpoint' else values
                        assert h.setSolution(len(start),np.arange(len(start),dtype=np.int32),start.astype(float))==highspy.HighsStatus.kOk
                    h.run();info=h.getInfo()
                    row=dict(m=m,seed=seed,version=h.version(),legacy=legacy,global_big_m=global_big_m,mode=mode,presolve=presolve,hint=hint,cp_count=cp.kappa_opt,
                             status=str(h.getModelStatus()),objective=info.objective_function_value,bound=info.mip_dual_bound,audit=check)
                    reports.append(row);print(json.dumps(row),flush=True)
                    (output/'report.json').write_text(json.dumps(reports,indent=2),encoding='utf-8', newline='\n')
    return reports


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--m',type=int,default=3);p.add_argument('--seed',type=int,default=2300);p.add_argument('--global-big-m',action='store_true');p.add_argument('--legacy',action='store_true')
    args=p.parse_args();run([(args.m,args.seed)],args.global_big_m,args.legacy)
