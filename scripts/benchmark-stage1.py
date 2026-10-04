"""Bounded repeated benchmark; every timeout retains the incumbent and bound."""
import argparse
import json
import statistics
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from certmorse.instances import load_instance,cost_values
from certmorse.landscape import exact_landscape,sample_landscape,make_band
from certmorse.complex import TorusComplex,lower_star_gradient
from certmorse.forman import witness
from certmorse.scaling import choose_scale,model_band,cell_band
from certmorse.mip import build_A,solve
from certmorse.mip.warm_start import simplified_hint
from certmorse.export_vtk import export_complex
from certmorse.runid import prepare_run
from certmorse.stage1 import complete

def run(limit=600,repeats=3,resume=False):
    inst=load_instance('R8a');started=time.perf_counter()
    truth,var,probs=exact_landscape(inst,32,'b',1003)
    landscape_s=time.perf_counter()-started
    mean,sv=sample_landscape((probs,cost_values(inst)),1000,np.random.default_rng(1003))
    lower,upper=make_band(mean,var,sv,1000,inst.W,.05,'oracle')
    scale,_=choose_scale(lower,upper);cx=TorusComplex(32)
    vlo,vhi=model_band(lower,upper,scale);lo,hi=cell_band(vlo,vhi,cx)
    rows=[]
    for trial in range(repeats):
        cfg=dict(experiment='stage1-benchmark-v1.7',instance='R8a',grid_m=32,noise='b',shots=1000,
                 band_mode='oracle',seed=1003+trial,time_limit_s=limit,repeats=repeats)
        path,needed=prepare_run(cfg,resume=resume)
        if not needed:
            rows.append(json.loads((path/'measurement.json').read_text()));continue
        mid=(vlo+vhi)/(2*scale)
        export_complex(cx,path/'band.vtu',{'Scalar':mid,'Lower':vlo/scale,'Upper':vhi/scale})
        a,b=lower_star_gradient(mid,cx)
        hint=dict(x=witness(a,b,lo,hi,cx),y=np.concatenate((a,b)),seed=1003+trial)
        candidate,status=simplified_hint(path/'band.vtu',path/'simplified.csv',float(np.min((vhi-vlo)/scale)),lo,hi,cx)
        used='midpoint'
        if candidate is not None and candidate['y'].sum()>=hint['y'].sum():
            hint={**candidate,'seed':1003+trial};used='ttk_simplified'
        result=solve(build_A(lo,hi,cx),'cpsat',limit,8,hint,str(path/'solver.log'))
        row={k:getattr(result,k) for k in ['status','kappa_lb','kappa_incumbent','kappa_opt','lb_is_certificate','bound','gap','wall_s','nodes']}
        row.update(run_id=path.name,trial=trial,warm_start_used=used,ttk_warm_status=status,
                   hint_count=cx.nc-2*int(hint['y'].sum()),field_seed=1003,solver_seed=1003+trial,time_limit_s=limit)
        np.savez_compressed(path/'solution.npz',x=result.x,y=result.y,lo=lo,hi=hi,mean=mean,truth=truth)
        (path/'measurement.json').write_text(json.dumps(row,indent=2),encoding='utf8');complete(path,solver_status=result.status)
        rows.append(row);print(json.dumps(row),flush=True)
    report=dict(instance='R8a',m=32,channel='b',shots=1000,band_mode='oracle',threads=8,
                density_matrix_landscape_s=landscape_s,requested_time_limit_s=limit,
                repeats=rows,median_solver_wall_s=statistics.median(r['wall_s'] for r in rows),
                grid_scaling_extrapolation_justified=False)
    Path('docs/benchmark-v1.7.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--limit',type=float,default=600);p.add_argument('--repeats',type=int,default=3);p.add_argument('--resume',action='store_true')
    args=p.parse_args();run(args.limit,args.repeats,args.resume)
