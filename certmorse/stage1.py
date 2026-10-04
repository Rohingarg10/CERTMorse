"""Resumable Stage 1 evidence; each invocation records its own config and status."""
import argparse
import csv
import json
import logging
from pathlib import Path
import time
import numpy as np
from .complex import TorusComplex, lower_star_gradient
from .forman import witness, NegativeCycle, is_discrete_morse
from .instances import load_instance, cost_values
from .landscape import exact_landscape, sample_landscape, make_band
from .scaling import choose_scale, model_band, cell_band
from .mip import build_A, solve, solve_B_lazy
from .mip.solvers import sample_optima, emit_highs
from .mip.bounds import persistence_bounds
from .mip.warm_start import simplified_hint
from .metrics import critical_counts, basin_probability
from .export_vtk import export_complex
from .ttk import execute, read_mandatory
from .runid import prepare_run
from .rng import streams
from .persistence import persistence, lower_star_values, bottleneck


def event(path, name, **payload):
    with (path/'log.jsonl').open('a',encoding='utf8') as stream:
        stream.write(json.dumps(dict(ts=time.time(),module='stage1',event=name,payload=payload))+'\n')


def complete(path, **payload):
    (path/'status.json').write_text(json.dumps(dict(complete=True,**payload),indent=2),encoding='utf8')


def r8a(bands=20, multiplicity_bands=10, resume=False, band_mode='oracle'):
    inst=load_instance('R8a')
    cx=TorusComplex(16)
    truth,var,probs=exact_landscape(inst,16,'a',1003)
    rows=[]
    for seed in range(bands):
        cfg=dict(experiment='stage1-r8a-v1.7-'+band_mode,instance='R8a',grid_m=16,seed=seed,
                 shots=1000,band_mode=band_mode,multiplicity={'enabled':seed<multiplicity_bands})
        # enabled is supplied by the normative config schema.
        path,run=prepare_run(cfg,resume=resume)
        if not run:
            rows.append(json.loads((path/'measurement.json').read_text(encoding='utf8')))
            continue
        rng=streams(seed)
        mean,sv=sample_landscape((probs,cost_values(inst)),1000,rng['land'])
        lower,upper=make_band(mean,var,sv,1000,inst.W,.05,band_mode)
        scale,n_widened=choose_scale(lower,upper)
        vlo,vhi=model_band(lower,upper,scale)
        lo,hi=cell_band(vlo,vhi,cx)
        model=build_A(lo,hi,cx)
        emit_highs(model).writeModel(str(path/'model.mps'))
        mid=(vlo+vhi)/(2*scale)
        a,b=lower_star_gradient(mid,cx)
        wx=witness(a,b,lo,hi,cx)
        if isinstance(wx,NegativeCycle): raise AssertionError('T15 midpoint witness failed')
        hint=dict(x=wx,y=np.concatenate((a,b)),seed=seed)
        midpoint_count=cx.nc-2*int(hint['y'].sum())
        refs=persistence_bounds(mid, vlo/scale, vhi/scale,cx)
        export_complex(cx,path/'band.vtu',{'Scalar':mid,'Lower':vlo/scale,'Upper':vhi/scale})
        delta=float(np.min((vhi-vlo)/(2*scale)))
        candidate,warm_status=simplified_hint(path/'band.vtu',path/'simplified.csv',2*delta,lo,hi,cx)
        warm_count=None if candidate is None else cx.nc-2*int(candidate['y'].sum())
        warm_source='midpoint'
        if candidate is not None and candidate['y'].sum()>=hint['y'].sum():
            hint={**candidate,'seed':seed};warm_source='ttk_simplified'
        result=solve(model,'cpsat',600,8,hint,str(path/'solver.log'))
        if result.y is None: raise AssertionError(result.status)
        aa,bb=cx.split_matching(result.y)
        assert is_discrete_morse(result.x,aa,bb,cx)[0]
        c0,c1,c2=critical_counts(result.y,cx)
        assert c0>=1 and c2>=1 and c1==c0+c2
        assert result.kappa_lb<=result.kappa_incumbent<=midpoint_count
        execute('mandatory',path/'band.vtu',path/'mandatory.csv')
        counts,_=read_mandatory(path/'mandatory.csv')
        lb_mand=max(4,2*(counts['MinimumComponents']+counts['MaximumComponents']))
        covered=bool(np.all((lower<=truth)&(truth<=upper)))
        true_ve,true_et=lower_star_gradient(truth,cx)
        kappa_true=cx.nc-2*int(true_ve.sum()+true_et.sum())
        rounded_ve,rounded_et=lower_star_gradient(np.rint(scale*truth).astype(np.int64),cx)
        kappa_true_rounded=cx.nc-2*int(rounded_ve.sum()+rounded_et.sum())
        transfer=witness(true_ve,true_et,lo,hi,cx)
        transfer_ok=not isinstance(transfer,NegativeCycle)
        flat_truth=truth.reshape(-1)
        sep_min=float(np.min(np.abs(flat_truth[cx.edge_vertices[:,0]]-flat_truth[cx.edge_vertices[:,1]]))*scale)
        if covered and sep_min>=14: assert transfer_ok
        if covered and transfer_ok:
            assert result.kappa_lb<=kappa_true
            if result.kappa_opt is not None: assert result.kappa_opt<=kappa_true
        row=dict(run_id=path.name,seed=seed,status=result.status,kappa_lb=result.kappa_lb,
                 kappa_incumbent=result.kappa_incumbent,kappa_opt=result.kappa_opt,
                 lb_is_certificate=result.lb_is_certificate,wall_s=result.wall_s,
                 scale=scale,n_widened=n_widened,coverage=covered,transfer_ok=transfer_ok,
                 transfer_claim=covered and transfer_ok,band_mode=band_mode,
                 simultaneous_band_guarantee=band_mode=='hoeffding',
                 sep_min=sep_min,kappa_true=kappa_true,kappa_true_rounded=kappa_true_rounded,LB_mand=lb_mand,**refs,
                 warm_start_used=warm_source,ttk_warm_status=warm_status,ttk_warm_count=warm_count,
                 UB_witness_justified=bool(candidate is not None and warm_count<=refs['UB_pers']),
                 bound_violation=result.kappa_incumbent<lb_mand,
                 d_B=None,
                 P_first=None,P_med=None,P_lo=None,P_hi=None,n_opt_found=0,
                 sampling_status='skipped_not_optimal' if result.status!='OPTIMAL' else 'not_requested')
        sampled=[]
        if result.status=='OPTIMAL':
            row['P_first']=basin_probability(result.y,mean,inst.W,cx)
            row['d_B']=bottleneck(persistence(result.x,cx,scale),persistence(lower_star_values(truth,cx),cx,1))
            if seed<multiplicity_bands:
                sampled,status=sample_optima(model,result.kappa_opt,20,300,rng['fc'],initial_result=result,log_path=str(path/'sampling.log'))
                values=[basin_probability(r.y,mean,inst.W,cx) for r in sampled]
                row.update(P_med=float(np.median(values)),P_lo=min(values),P_hi=max(values),n_opt_found=len(values),sampling_status=status)
        np.savez_compressed(path/'matching.npz',x=result.x,y=result.y,lower=lower,upper=upper,cell_lo=lo,cell_hi=hi,mean=mean,truth=truth,optima=np.array([r.y for r in sampled]))
        (path/'measurement.json').write_text(json.dumps(row,indent=2),encoding='utf8')
        event(path,'measurement',**row)
        complete(path,solver_status=result.status)
        rows.append(row)
        print(json.dumps(row),flush=True)
    output=Path('docs/stage1-r8a-v1.7-'+band_mode+'.csv')
    with output.open('w',newline='',encoding='utf8') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    return rows


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--bands',type=int,default=20)
    parser.add_argument('--multiplicity-bands',type=int,default=10)
    parser.add_argument('--resume',action='store_true')
    parser.add_argument('--band-mode',choices=['oracle','hoeffding','empirical'],default='oracle')
    args=parser.parse_args()
    r8a(args.bands,args.multiplicity_bands,args.resume,args.band_mode)
