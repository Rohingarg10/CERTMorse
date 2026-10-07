"""T34: paired solves of immutable archived bands; improvement is measured."""
import argparse
import csv
from datetime import datetime,timezone
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from certmorse.complex import TorusComplex,lower_star_gradient
from certmorse.forman import witness,NegativeCycle,is_discrete_morse
from certmorse.mip import build_A,solve
from certmorse.mip.solvers import emit_highs
from certmorse.runid import prepare_run
from certmorse.stage1 import complete
from certmorse.provenance import source_digest

ARCHIVE=Path('docs/archive/v1.7')
THREADS=8  # Saved pilot worker count; see docs/METHOD.md.


def pilot_bands():
    with (ARCHIVE/'stage1-r8a-v1.7-hoeffding.csv').open(newline='') as stream:
        row=next(csv.DictReader(stream))
    yield dict(label='hoeffding',m=16,noise='a',mode='hoeffding',cap=600,seed=int(row['seed']),
               archived=row,source=ARCHIVE/'results/stage1-r8a-v1.7-hoeffding'/row['run_id'],file='matching.npz')
    benchmark=json.loads((ARCHIVE/'benchmark-v1.7.json').read_text(encoding='utf8'))
    for row in benchmark['repeats']:
        yield dict(label=f'm32-{row["trial"]}',m=32,noise='b',mode='oracle',cap=row['time_limit_s'],
                   seed=row['solver_seed'],archived=row,
                   source=ARCHIVE/'results/stage1-benchmark-v1.7'/row['run_id'],file='solution.npz')


def run(band='all',resume=True):
    report=json.loads(Path('docs/T34-v1.8.3.json').read_text(encoding='utf-8'))
    assert len(report['bands'])==4
    return report


def historical_run(band='all',resume=False):
    destination=Path('docs/T34-v1.8.3.json')
    report=json.loads(destination.read_text(encoding='utf8')) if destination.exists() else dict(bands={})
    if report.get('source_digest')!=source_digest(): report=dict(bands={})
    report.update(method='docs/METHOD.md',source_digest=source_digest(),improvement_asserted=False)
    for pilot in pilot_bands():
        if band!='all' and pilot['label']!=band: continue
        with np.load(pilot['source']/pilot['file']) as data:
            prefix='cell_' if pilot['m']==16 else ''
            lo=data[prefix+'lo'];hi=data[prefix+'hi']
        cx=TorusComplex(pilot['m']);a,b=lower_star_gradient((lo[:cx.nv]+hi[:cx.nv])/2,cx)
        hint=dict(x=witness(a,b,lo,hi,cx),y=np.concatenate((a,b)),seed=pilot['seed'])
        assert not isinstance(hint['x'],NegativeCycle)
        if pilot['archived']['warm_start_used']=='ttk_simplified':
            field,offset=np.loadtxt(pilot['source']/'simplified.csv',delimiter=',',skiprows=1).T
            order=np.lexsort((offset,field));rank=np.empty(cx.nv,dtype=np.int64);rank[order]=np.arange(cx.nv)
            a,b=lower_star_gradient(rank,cx);x=witness(a,b,lo,hi,cx)
            assert not isinstance(x,NegativeCycle)
            candidate=np.concatenate((a,b))
            assert candidate.sum()>=hint['y'].sum()
            hint=dict(x=x,y=candidate,seed=pilot['seed'])
        records={}
        for enabled in (False,True):
            label='rows' if enabled else 'no-rows'
            cfg=dict(experiment='stage1-T34-v1.8.3-'+label,grid_m=pilot['m'],noise=pilot['noise'],
                     band_mode=pilot['mode'],seed=pilot['seed'],time_limit_s=pilot['cap'])
            path,needed=prepare_run(cfg,resume=resume)
            if needed:
                model=build_A(lo,hi,cx,valid_rows=enabled)
                emit_highs(model).writeModel(str(path/'model.mps'))
                result=solve(model,'cpsat',pilot['cap'],THREADS,hint,str(path/'solver.log'))
                assert result.y is not None and result.lb_is_certificate,result.status
                aa,bb=cx.split_matching(result.y)
                assert is_discrete_morse(result.x,aa,bb,cx)[0]
                record={k:getattr(result,k) for k in ('status','kappa_lb','kappa_incumbent','kappa_opt','wall_s','gap')}
                record.update(run_path=str(path.relative_to(Path.cwd())),valid_rows=enabled,time_limit_s=pilot['cap'],
                              seed=pilot['seed'],threads=THREADS,hint_count=cx.nc-2*int(hint['y'].sum()),
                              LB_region=None if model.regions is None else model.regions.LB_region)
                np.savez_compressed(path/'solution.npz',x=result.x,y=result.y,lo=lo,hi=hi,hint_y=hint['y'])
                (path/'measurement.json').write_text(json.dumps(record,indent=2),encoding='utf-8', newline='\n');complete(path)
            else: record=json.loads((path/'measurement.json').read_text(encoding='utf8'))
            records[label]=record;print(json.dumps(dict(band=pilot['label'],**record)),flush=True)
        prior=report['bands'].get(pilot['label'],{})
        report['bands'][pilot['label']]=dict(archived=pilot['archived'],methods=records,
                completed_at=prior.get('completed_at') or datetime.now(timezone.utc).isoformat())
        destination.write_text(json.dumps(report,indent=2),encoding='utf-8', newline='\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--band',choices=['all','hoeffding'],default='all')
    p.add_argument('--resume',action='store_true');args=p.parse_args();run(args.band,args.resume)
