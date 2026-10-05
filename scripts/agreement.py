"""T33: 120 identical bands, three methods, with and without v1.8 rows."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from certmorse.complex import TorusComplex,lower_star_gradient
from certmorse.forman import witness
from certmorse.scaling import choose_scale,model_band,cell_band
from certmorse.mip import build_A,build_B,solve,solve_B_lazy
from certmorse.mip.regions import region_bound
from certmorse.mip.solvers import emit_highs
from certmorse.runid import prepare_run
from certmorse.stage1 import event,complete

TIME_LIMIT_S = 600  # v1.6 solver protocol, retained by v1.8.
THREADS = 8  # v1.6 solver protocol.


def passed(row):
    methods=row['methods']
    return (set(methods)=={'cpsatA','highsA','cpsatB'} and
            all(r['status']=='OPTIMAL' and r['kappa_opt'] is not None for r in methods.values()) and
            len({r['kappa_opt'] for r in methods.values()})==1)


def run(grids,resume=False):
    results=[]
    for m in grids:
        for seed in range(20 if m==8 else 50):
            rng=np.random.default_rng(2300+seed);cx=TorusComplex(m)
            g=rng.normal(size=cx.nv);width=rng.uniform(.01,.5,size=cx.nv)
            scale,_=choose_scale(g-width,g+width)
            lo,hi=cell_band(*model_band(g-width,g+width,scale),cx)
            regions=region_bound(lo,hi,cx)
            a,b=lower_star_gradient(g,cx)
            hint=dict(x=witness(a,b,lo,hi,cx),y=np.concatenate((a,b)),seed=seed)
            row=dict(m=m,seed=seed,methods={},controls={})
            for rows_enabled in (False,True):
                for backend,form in [('cpsat','A'),('highs','A'),('cpsat','B')]:
                    label='rows' if rows_enabled else 'no-rows'
                    cfg=dict(experiment='stage1-agreement-v1.8.3-'+label,grid_m=m,seed=2300+seed,
                             solver=backend,formulation=form)
                    path,needed=prepare_run(cfg,resume=resume)
                    if needed:
                        if form=='A':
                            model=build_A(lo,hi,cx,valid_rows=rows_enabled)
                            emit_highs(model).writeModel(str(path/'model.mps'))
                            result=solve(model,backend,TIME_LIMIT_S,THREADS,hint,str(path/'solver.log'))
                        else:
                            model=build_B(cx,valid_rows=rows_enabled)
                            if rows_enabled: model.regions=regions
                            result=solve_B_lazy(cx,lo,hi,backend,TIME_LIMIT_S,THREADS,hint,str(path/'solver.log'),
                                                valid_rows=rows_enabled,cut_callback=lambda family,cut,y:model.cuts.append(cut))
                            emit_highs(model).writeModel(str(path/'model.mps'))
                        record={key:getattr(result,key) for key in ('status','kappa_incumbent','kappa_lb','kappa_opt',
                                'lb_is_certificate','bound','gap','wall_s','cut_iters','cuts_added')}
                        record.update(run_path=str(path.relative_to(Path.cwd())),valid_rows=rows_enabled,LB_region=regions.LB_region)
                        np.savez_compressed(path/'solution.npz',x=result.x,y=result.y,lo=lo,hi=hi,g=g,width=width)
                        (path/'measurement.json').write_text(json.dumps(record,indent=2),encoding='utf8')
                        event(path,'agreement',**record);complete(path,solver_status=result.status)
                    else: record=json.loads((path/'measurement.json').read_text(encoding='utf8'))
                    row['methods' if rows_enabled else 'controls'][backend+form]=record
            row['agree']=passed(row) and passed(dict(methods=row['controls']))
            row['rows_preserve_optimum']=all(row['methods'][method]['kappa_opt']==row['controls'][method]['kappa_opt']
                                            for method in row['methods'])
            row['all_optimal']=all(r['status']=='OPTIMAL' for family in ['methods','controls'] for r in row[family].values())
            results.append(row)
            Path('docs/agreement-v1.8.3.json').write_text(json.dumps(results,indent=2),encoding='utf8')
            print(json.dumps(row),flush=True)
            assert row['agree'] and row['rows_preserve_optimum'], 'T33 failed; see saved exact bands and witnesses'
    return results


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--grids',type=int,nargs='+',default=[3,4,8])
    parser.add_argument('--resume',action='store_true');args=parser.parse_args();run(args.grids,args.resume)
