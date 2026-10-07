"""Stage 1 measurements and saved-result checks; see docs/METHOD.md."""
import argparse
import csv
import json
from pathlib import Path
import time
import numpy as np
from .complex import TorusComplex,lower_star_gradient
from .forman import witness,NegativeCycle,is_discrete_morse
from .instances import load_instance,cost_values
from .landscape import exact_landscape,sample_landscape,make_band,measured_symmetry,BETA_PERIODS
from .scaling import choose_scale,model_band,cell_band
from .mip import build_A,solve
from .mip.solvers import sample_optima,emit_highs
from .mip.bounds import persistence_bounds,truth_count
from .mip.warm_start import simplified_hint
from .metrics import critical_counts,basin_probability
from .export_vtk import export_complex
from .ttk import execute,read_mandatory
from .runid import prepare_run
from .rng import streams
from .persistence import persistence,lower_star_values,bottleneck
from .resolution import resolution_check

GRID_M = 16  # Measured Stage 1 grid size.
SHOTS = 1000  # Shots per vertex in the reported band.
ALPHA = 0.05  # Simultaneous band error budget.
FIELD_SEED = 1003  # Saved Stage 1 field/transpilation seed.
TIME_LIMIT_S = 600  # Count-solve cap in seconds.
THREADS = 8  # Retained solver protocol.
MAX_OPTIMA = 20  # Requested optima per sampled band.
SAMPLING_CAP_S = 300  # Sampling cap per band in seconds.
TRANSFER_MARGIN = 14  # Outward integer margin for matching transfer.


def event(path,name,**payload):
    with (path/'log.jsonl').open('a',encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(dict(ts=time.time(),module='stage1',event=name,payload=payload))+'\n')


def complete(path,**payload):
    (path/'status.json').write_text(json.dumps(dict(complete=True,**payload),indent=2),encoding='utf-8', newline='\n')


def measure_instance(instance,bands=20,multiplicity_bands=10,resume=True,band_mode='hoeffding'):
    saved=Path(f'docs/stage1-{instance.lower()}-v1.8.3-{band_mode}.csv')
    if saved.exists():
        with saved.open(encoding='utf-8',newline='\n') as stream:
            rows=list(csv.DictReader(stream))
        assert len(rows)>=bands
        return rows[:bands]
    raise RuntimeError('use separate raw units for missing bands; completed Stage 1 solves are read-only')


def historical_measure_instance(instance,bands=20,multiplicity_bands=10,resume=False,band_mode='hoeffding'):
    inst=load_instance(instance);cx=TorusComplex(GRID_M)
    truth,var,probs=exact_landscape(inst,GRID_M,'a',FIELD_SEED)
    symmetry=measured_symmetry(inst,'a',FIELD_SEED)
    resolution=resolution_check(inst,truth,'a',FIELD_SEED)
    rows=[]
    for seed in range(bands):
        cfg=dict(experiment=f'stage1-{instance.lower()}-v1.8.3-{band_mode}',instance=instance,
                 grid_m=GRID_M,seed=seed,shots=SHOTS,band_mode=band_mode,
                 multiplicity={'enabled':seed<multiplicity_bands})
        path,needed=prepare_run(cfg,resume=resume)
        if not needed:
            rows.append(json.loads((path/'measurement.json').read_text(encoding='utf8')));continue
        rng=streams(seed);mean,sv=sample_landscape((probs,cost_values(inst)),SHOTS,rng['land'])
        lower,upper=make_band(mean,var,sv,SHOTS,inst.W,ALPHA,band_mode)
        scale,n_widened=choose_scale(lower,upper)
        vlo,vhi=model_band(lower,upper,scale);lo,hi=cell_band(vlo,vhi,cx)
        model=build_A(lo,hi,cx);regions=model.regions
        emit_highs(model).writeModel(str(path/'model.mps'))
        mid=(vlo+vhi)/(2*scale);a,b=lower_star_gradient(mid,cx);wx=witness(a,b,lo,hi,cx)
        assert not isinstance(wx,NegativeCycle), 'T15 midpoint witness failed'
        hint=dict(x=wx,y=np.concatenate((a,b)),seed=seed)
        midpoint_count=cx.nc-2*int(hint['y'].sum())
        refs=persistence_bounds(mid,vlo/scale,vhi/scale,cx)
        export_complex(cx,path/'band.vtu',{'Scalar':mid,'Lower':vlo/scale,'Upper':vhi/scale},
                       beta_period=BETA_PERIODS['a'],qaoa=True)
        delta=float(np.min((vhi-vlo)/(2*scale)))
        candidate,warm_status=simplified_hint(path/'band.vtu',path/'simplified.csv',2*delta,lo,hi,cx)
        warm_count=None if candidate is None else cx.nc-2*int(candidate['y'].sum())
        warm_source='midpoint'
        if candidate is not None and candidate['y'].sum()>=hint['y'].sum():
            hint={**candidate,'seed':seed};warm_source='ttk_simplified'
        result=solve(model,'cpsat',TIME_LIMIT_S,THREADS,hint,str(path/'solver.log'))
        assert result.y is not None, result.status
        aa,bb=cx.split_matching(result.y)
        assert is_discrete_morse(result.x,aa,bb,cx)[0]
        c0,c1,c2=critical_counts(result.y,cx)
        assert c0>=1 and c2>=1 and c1==c0+c2
        assert result.kappa_lb<=result.kappa_incumbent<=midpoint_count
        assert regions.LB_region<=result.kappa_incumbent
        execute('mandatory',path/'band.vtu',path/'mandatory.csv')
        counts,_=read_mandatory(path/'mandatory.csv')
        lb_mand=max(4,2*(counts['MinimumComponents']+counts['MaximumComponents']))
        covered=bool(np.all((lower<=truth)&(truth<=upper)))
        diagnostics=truth_count(truth,cx,scale,str(path/'kappa-zero.log'))
        true_ve,true_et=lower_star_gradient(truth,cx)
        true_count=cx.nc-2*int(true_ve.sum()+true_et.sum())
        transfer_ok=not isinstance(witness(true_ve,true_et,lo,hi,cx),NegativeCycle)
        if covered and diagnostics['sep_min_units']>=TRANSFER_MARGIN: assert transfer_ok
        kappa_cert=max(result.kappa_lb,regions.LB_region)
        if covered and transfer_ok:
            assert kappa_cert<=true_count
            if result.kappa_opt is not None: assert result.kappa_opt<=true_count
        row=dict(run_id=path.name,instance=instance,grid_m=GRID_M,noise='a',shots=SHOTS,alpha=ALPHA,
                 seed=seed,field_seed=FIELD_SEED,status=result.status,kappa_lb=result.kappa_lb,
                 kappa_incumbent=result.kappa_incumbent,kappa_opt=result.kappa_opt,kappa_cert=kappa_cert,
                 lb_is_certificate=result.lb_is_certificate,bound=result.bound,gap=result.gap,
                 wall_s=result.wall_s,nodes=result.nodes,cut_iters=result.cut_iters,cuts_added=result.cuts_added,
                 c0=c0,c1=c1,c2=c2,scale=scale,n_widened=n_widened,coverage=covered,
                 transfer_ok=transfer_ok,transfer_claim=covered and transfer_ok,band_mode=band_mode,
                 simultaneous_band_guarantee=band_mode=='hoeffding',**diagnostics,
                 sep_min=diagnostics['sep_min_units'],LB_mand=lb_mand,**refs,LB_region=regions.LB_region,
                 region_minima=len(regions.minimum_regions),region_maxima=len(regions.maximum_regions),
                 warm_start_used=warm_source,ttk_warm_status=warm_status,ttk_warm_count=warm_count,
                 UB_witness_justified=bool(candidate is not None and warm_count<=refs['UB_pers']),
                 bound_violation=result.kappa_incumbent<lb_mand,**symmetry,
                 P0=resolution['P0_grid'],P0_grid=resolution['P0_grid'],P0_cont=resolution['P0_cont'],
                 resolution_adequate=resolution['resolution_adequate'],
                 worst_grid_depth_error=resolution['worst_grid_depth_error'],
                 RQ2_informative=resolution['RQ2_informative'],
                 basin_conclusion_eligible=resolution['resolution_adequate'],d_B=None,
                 P_first=None,P_possible=None,P_med=None,P_lo=None,P_hi=None,n_opt_found=0,
                 sampling_status='skipped_not_optimal' if result.status!='OPTIMAL' else 'not_requested')
        for name in ('kappa_true','kappa_incumbent','kappa_lb','kappa_opt','kappa_cert'):
            count=row[name]
            row[name+'_per_copy']=None if count is None or count%symmetry['copies'] else count//symmetry['copies']
        sampled=[];sample_values=[];sample_possible=[]
        if result.status=='OPTIMAL':
            row['P_first'],row['P_possible']=basin_probability(result.y,mean,inst.W,cx,lower,upper)
            row['d_B']=bottleneck(persistence(result.x,cx,scale),persistence(lower_star_values(truth,cx),cx,1))
            if seed<multiplicity_bands:
                sampled,status=sample_optima(model,result.kappa_opt,MAX_OPTIMA,SAMPLING_CAP_S,rng['fc'],
                                             initial_result=result,log_path=str(path/'sampling.log'))
                for sample in sampled:
                    P,possible=basin_probability(sample.y,mean,inst.W,cx,lower,upper)
                    sample_values.append(P);sample_possible.append(possible)
                row.update(P_med=float(np.median(sample_values)),P_lo=min(sample_values),P_hi=max(sample_values),
                           n_opt_found=len(sample_values),sampling_status=status)
        np.savez_compressed(path/'matching.npz',x=result.x,y=result.y,lower=lower,upper=upper,cell_lo=lo,cell_hi=hi,
                            mean=mean,truth=truth,optima=np.array([r.y for r in sampled],dtype=np.int8).reshape(-1,len(cx.pairs)),
                            sample_P=np.array(sample_values),sample_P_possible=np.array(sample_possible),
                            metadata=json.dumps(dict(**symmetry,**resolution,**diagnostics)))
        (path/'resolution.json').write_text(json.dumps(resolution,indent=2),encoding='utf-8', newline='\n')
        (path/'measurement.json').write_text(json.dumps(row,indent=2),encoding='utf-8', newline='\n')
        if instance=='R8a' and result.status=='OPTIMAL':
            assert row['P_first']==1 and all(P==1 for P in sample_values), 'T32 R8a control failed; artifact preserved'
        event(path,'measurement',**row);complete(path,solver_status=result.status);rows.append(row)
        print(json.dumps(row),flush=True)
    destination=Path(f'docs/stage1-{instance.lower()}-v1.8.3-{band_mode}.csv')
    with destination.open('w',newline='\n',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]), lineterminator='\n');writer.writeheader();writer.writerows(rows)
    return rows


def r8a(bands=20,multiplicity_bands=10,resume=False,band_mode='hoeffding'):
    return measure_instance('R8a',bands,multiplicity_bands,resume,band_mode)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--bands',type=int,default=20)
    parser.add_argument('--multiplicity-bands',type=int,default=10);parser.add_argument('--resume',action='store_true')
    parser.add_argument('--instances',nargs='+',choices=['R8a','E8a','W8a'],default=['R8a','E8a','W8a'])
    parser.add_argument('--band-mode',choices=['oracle','hoeffding','empirical'],default='hoeffding')
    args=parser.parse_args()
    for instance in args.instances:
        measure_instance(instance,args.bands,args.multiplicity_bands,args.resume,args.band_mode)
