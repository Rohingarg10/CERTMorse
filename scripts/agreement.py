"""Full-sized Stage 1 cross-method checks, separate from quick unit tests."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from certmorse.complex import TorusComplex, lower_star_gradient
from certmorse.forman import witness
from certmorse.scaling import choose_scale, model_band, cell_band
from certmorse.mip import build_A, solve, solve_B_lazy
from certmorse.runid import prepare_run
from certmorse.stage1 import event, complete


def passed(row):
    methods=row['methods']
    return (set(methods)=={'cpsatA','highsA','cpsatB'} and
            all(r['status']=='OPTIMAL' and r['kappa_opt'] is not None for r in methods.values()) and
            len({r['kappa_opt'] for r in methods.values()})==1)


def run(grids, resume=False):
    results=[]
    failed=False
    for m in grids:
        for seed in range(20 if m==8 else 50):
            rng=np.random.default_rng(2300+seed)
            cx=TorusComplex(m)
            g=rng.normal(size=cx.nv)
            width=rng.uniform(.01,.5,size=cx.nv)
            scale,_=choose_scale(g-width,g+width)
            lo,hi=cell_band(*model_band(g-width,g+width,scale),cx)
            a,b=lower_star_gradient(g,cx)
            hint=dict(x=witness(a,b,lo,hi,cx),y=np.concatenate((a,b)),seed=seed)
            row=dict(m=m,seed=seed,methods={})
            for backend,form in [('cpsat','A'),('highs','A'),('cpsat','B')]:
                cfg=dict(experiment='stage1-agreement-v1.7',grid_m=m,seed=2300+seed,solver=backend,formulation=form)
                path,needed=prepare_run(cfg,resume=resume)
                if needed:
                    model=build_A(lo,hi,cx)
                    result=solve(model,backend,600,8,hint,str(path/'solver.log')) if form=='A' else solve_B_lazy(cx,lo,hi,backend,600,8,hint,str(path/'solver.log'))
                    record={key:getattr(result,key) for key in ('status','kappa_incumbent','kappa_lb','kappa_opt','lb_is_certificate','bound','gap','wall_s','cut_iters','cuts_added')}
                    record['run_path']=str(path.relative_to(Path.cwd()))
                    np.savez_compressed(path/'solution.npz',x=result.x,y=result.y,lo=lo,hi=hi,g=g,width=width)
                    (path/'measurement.json').write_text(json.dumps(record,indent=2),encoding='utf8')
                    event(path,'agreement',**record);complete(path,solver_status=result.status)
                else: record=json.loads((path/'measurement.json').read_text(encoding='utf8'))
                row['methods'][backend+form]=record
            optimal=[r['kappa_opt'] for r in row['methods'].values() if r['status']=='OPTIMAL']
            row['agree']=len(set(optimal))<=1
            row['all_optimal']=len(optimal)==3
            results.append(row)
            print(json.dumps(row),flush=True)
            Path('docs/agreement-v1.7.json').write_text(json.dumps(results,indent=2),encoding='utf8')
            failed=failed or not passed(row)
    if failed: raise AssertionError('agreement gate requires matching OPTIMAL counts from all three methods; see saved evidence')
    return results


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--grids',type=int,nargs='+',default=[3,4,8]);p.add_argument('--resume',action='store_true')
    args=p.parse_args();run(args.grids,args.resume)
