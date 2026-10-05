"""Executable Stage 1 gate, v1.8 with amendments through v1.8.3."""
import csv
from datetime import datetime,timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import yaml
from certmorse.complex import TorusComplex,lower_star_gradient
from certmorse.forman import witness,NegativeCycle,is_discrete_morse
from certmorse.metrics import basin_probability,critical_counts
from certmorse.instances import load_instance
from certmorse.provenance import source_digest
from certmorse.mip.regions import region_bound
from certmorse.resolution import RESOLUTION_INSTANCES,GRID_SIZES,INFORMATIVE_LIMIT
from scripts.agreement import passed


def run():
    started=datetime.now(timezone.utc)
    output=Path('results/stage1-gate-v1.8.3')/started.strftime('%Y%m%dT%H%M%SZ')
    output.mkdir(parents=True,exist_ok=True)
    report=dict(specification='v1.8',amendments=['v1.8.1','v1.8.2','v1.8.3'],
                started_at=started.isoformat(),source_digest=source_digest(),status='RUNNING',
                full_gate_ran=True,steps=[],checks={})
    destination=Path('docs/stage1-gate.json')
    def save(): destination.write_text(json.dumps(report,indent=2),encoding='utf-8', newline='\n')
    def verify(path):
        assert yaml.safe_load((path/'config.yaml').read_text(encoding='utf8'))['source_digest']==report['source_digest']
        assert json.loads((path/'status.json').read_text(encoding='utf8'))['complete']
    def verify_matching(cx,x,y,lo,hi,count):
        a,b=cx.split_matching(y)
        assert is_discrete_morse(x,a,b,cx)[0]
        assert np.all((lo<=x)&(x<=hi))
        assert cx.nc-2*int(y.sum())==count
        assert not isinstance(witness(a,b,lo,hi,cx),NegativeCycle)
    save()
    commands=[('tests',[sys.executable,'-m','pytest','-q','-x','--junitxml='+str(output/'tests.xml')]),
              ('agreement',[sys.executable,'scripts/agreement.py','--resume']),
              ('resolution',[sys.executable,'scripts/resolution-study.py','--resume']),
              ('hoeffding',[sys.executable,'-m','certmorse.stage1','--resume']),
              ('oracle',[sys.executable,'-m','certmorse.stage1','--instances','R8a','--band-mode','oracle',
                         '--multiplicity-bands','0','--resume']),
              ('coverage',[sys.executable,'scripts/coverage-study.py'])]
    try:
        t34=json.loads(Path('docs/T34-v1.8.3.json').read_text(encoding='utf8'))
        assert t34['source_digest']==report['source_digest']
        assert datetime.fromisoformat(t34['bands']['hoeffding']['completed_at'])<started
        report['checks']['T34_hoeffding_before_gate']=t34['bands']['hoeffding'];save()
        for name,command in commands:
            print(f'Running {name}',flush=True);start=time.perf_counter()
            log=output/(name+'.log')
            with log.open('w',encoding='utf-8', newline='\n') as stream:
                result=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT)
            report['steps'].append(dict(name=name,command=command,exit_code=result.returncode,
                                       wall_s=time.perf_counter()-start,log=str(log)));save()
            if result.returncode: raise AssertionError(f'{name} failed; see {log}')
            if name=='tests':
                cases=ET.parse(output/'tests.xml').findall('.//testcase')
                assert cases and not any(c.find('skipped') is not None for c in cases),'required integrations must not be skipped'
                report['checks']['tests']=dict(passed=len(cases),skipped=0);save()
        cases=ET.parse(output/'tests.xml').findall('.//testcase')
        assert cases and not any(c.find('skipped') is not None for c in cases),'required integrations must not be skipped'
        assert not any(c.find('failure') is not None or c.find('error') is not None for c in cases)
        report['checks']['tests']=dict(passed=len(cases),skipped=0)
        rows=json.loads(Path('docs/agreement-v1.8.3.json').read_text(encoding='utf8'))
        assert {(r['m'],r['seed']) for r in rows}=={(m,s) for m in [3,4,8] for s in range(20 if m==8 else 50)}
        assert len(rows)==120 and all(passed(r) and passed(dict(methods=r['controls'])) and r['rows_preserve_optimum'] for r in rows)
        for row in rows:
            cx=TorusComplex(row['m'])
            for family in ('methods','controls'):
                for record in row[family].values():
                    path=Path(record['run_path']);verify(path)
                    with np.load(path/'solution.npz') as data:
                        verify_matching(cx,data['x'],data['y'],data['lo'],data['hi'],record['kappa_opt'])
        report['checks']['agreement']=dict(bands=120,optimal_solves=720,exact_witnesses_verified=720,
                                          valid_rows_preserve_all_optima=True)
        t34=json.loads(Path('docs/T34-v1.8.3.json').read_text(encoding='utf8'))
        assert set(t34['bands'])=={'hoeffding','m32-0','m32-1','m32-2'}
        for pilot in t34['bands'].values():
            for record in pilot['methods'].values():
                path=Path(record['run_path']);verify(path)
                with np.load(path/'solution.npz') as data:
                    m=yaml.safe_load((path/'config.yaml').read_text(encoding='utf8'))['grid_m']
                    verify_matching(TorusComplex(m),data['x'],data['y'],data['lo'],data['hi'],record['kappa_incumbent'])
        report['checks']['T34']=t34
        resolution=json.loads(Path('docs/resolution-v1.8.3.json').read_text(encoding='utf8'))
        assert resolution['source_digest']==report['source_digest']
        assert {(r['instance'],r['grid_m']) for r in resolution['rows']}=={(i,m) for i in RESOLUTION_INSTANCES for m in GRID_SIZES}
        assert len(resolution['rows'])==20
        for r in resolution['rows']:
            verify(Path(r['run_path']))
            assert r['resolution_adequate']==(r['grid_global']==r['continuous_global'])
            assert r['RQ2_informative']==(r['resolution_adequate'] and r['P0_grid']<=INFORMATIVE_LIMIT)
        report['checks']['resolution']=resolution
        summaries={};failures=[]
        for instance,mode in [('R8a','hoeffding'),('E8a','hoeffding'),('W8a','hoeffding'),('R8a','oracle')]:
            with Path(f'docs/stage1-{instance.lower()}-v1.8.3-{mode}.csv').open(newline='') as stream:
                measurements=list(csv.DictReader(stream))
            assert len(measurements)==20 and {int(r['seed']) for r in measurements}==set(range(20))
            cx=TorusComplex(16);inst=load_instance(instance);ranges=[];sample_total=0
            for row in measurements:
                path=Path(f'results/stage1-{instance.lower()}-v1.8.3-{mode}')/row['run_id'];verify(path)
                with np.load(path/'matching.npz') as data:
                    field,offset=np.loadtxt(path/'simplified.csv',delimiter=',',skiprows=1).T
                    assert len(np.unique(offset))==cx.nv
                    order=np.lexsort((offset,field));rank=np.empty(cx.nv,dtype=np.int64);rank[order]=np.arange(cx.nv)
                    wa,wb=lower_star_gradient(rank,cx)
                    warm=witness(wa,wb,data['cell_lo'],data['cell_hi'],cx)
                    accepted=not isinstance(warm,NegativeCycle)
                    assert accepted==(row['ttk_warm_status']=='accepted')
                    warm_count=cx.nc-2*int(wa.sum()+wb.sum())
                    assert (int(row['ttk_warm_count'])==warm_count) if accepted else not row['ttk_warm_count']
                    midpoint=(data['cell_lo'][:cx.nv]+data['cell_hi'][:cx.nv])/2
                    ma,mb=lower_star_gradient(midpoint,cx)
                    expected='ttk_simplified' if accepted and wa.sum()+wb.sum()>=ma.sum()+mb.sum() else 'midpoint'
                    assert row['warm_start_used']==expected
                    assert (row['UB_witness_justified']=='True')==(accepted and warm_count<=int(row['UB_pers']))
                    verify_matching(cx,data['x'],data['y'],data['cell_lo'],data['cell_hi'],int(row['kappa_incumbent']))
                    counts=critical_counts(data['y'],cx)
                    assert counts==tuple(int(row[k]) for k in ('c0','c1','c2'))
                    regions=region_bound(data['cell_lo'],data['cell_hi'],cx)
                    assert regions.LB_region==int(row['LB_region'])<=int(row['kappa_incumbent'])
                    assert int(row['kappa_cert'])==max(int(row['kappa_lb']),regions.LB_region)
                    assert int(row['kappa_cert'])<=int(row['kappa_incumbent'])
                    ta,tb=lower_star_gradient(data['truth'],cx)
                    transfer=not isinstance(witness(ta,tb,data['cell_lo'],data['cell_hi'],cx),NegativeCycle)
                    covered=bool(np.all((data['lower']<=data['truth'])&(data['truth']<=data['upper'])))
                    assert (row['transfer_claim']=='True')==(covered and transfer)
                    assert (row['coverage']=='True')==covered and (row['transfer_ok']=='True')==transfer
                    if covered and transfer: assert int(row['kappa_cert'])<=cx.nc-2*int(ta.sum()+tb.sum())
                    if row['status']=='OPTIMAL':
                        assert row['kappa_opt'] and int(row['kappa_opt'])==int(row['kappa_incumbent'])
                        P,possible=basin_probability(data['y'],data['mean'],inst.W,cx,data['lower'],data['upper'])
                        assert P==float(row['P_first']) and possible==float(row['P_possible'])
                    else:
                        assert not row['kappa_opt'] and not row['P_first'] and not row['P_possible']
                    optima=data['optima'];assert len(optima)==int(row['n_opt_found'])
                    assert len(np.unique(optima[:,:len(cx.pairs_ve)],axis=0))==len(optima)
                    values=[]
                    for y in optima:
                        assert row['status']=='OPTIMAL'
                        aa,bb=cx.split_matching(y);x=witness(aa,bb,data['cell_lo'],data['cell_hi'],cx)
                        assert not isinstance(x,NegativeCycle)
                        verify_matching(cx,x,y,data['cell_lo'],data['cell_hi'],int(row['kappa_opt']))
                        values.append(basin_probability(y,data['mean'],inst.W,cx,data['lower'],data['upper'])[0])
                    if values:
                        np.testing.assert_allclose([min(values),np.median(values),max(values)],
                                                   [float(row[k]) for k in ('P_lo','P_med','P_hi')],rtol=0,atol=0)
                        ranges.append(max(values)-min(values));sample_total+=len(values)
                    if instance=='R8a' and row['status']=='OPTIMAL': assert P==1 and all(v==1 for v in values)
                    assert row['basin_conclusion_eligible']==row['resolution_adequate']
                    assert row['bound_violation']==str(int(row['kappa_incumbent'])<int(row['LB_mand']))
            optimal=[r for r in measurements if r['status']=='OPTIMAL']
            sampled=[r for r in measurements if int(r['n_opt_found'])]
            summary=dict(bands=20,optimal=len(optimal),timeouts=sum(r['status']!='OPTIMAL' for r in measurements),
                count_bound_range=[min(int(r['kappa_lb']) for r in measurements),max(int(r['kappa_lb']) for r in measurements)],
                incumbent_range=[min(int(r['kappa_incumbent']) for r in measurements),max(int(r['kappa_incumbent']) for r in measurements)],
                kappa_equals_region=sum(int(r['kappa_opt'])==int(r['LB_region']) for r in optimal),optimal_denominator=len(optimal),
                region_equals_mandatory=sum(int(r['LB_region'])==int(r['LB_mand']) for r in measurements),
                mandatory_violations=sum(r['bound_violation']=='True' for r in measurements),
                multiplicity_bands=len(ranges),sampled_optima=sample_total,
                sample_count_range=None if not sampled else [min(int(r['n_opt_found']) for r in sampled),max(int(r['n_opt_found']) for r in sampled)],
                sampling_status_counts={status:sum(r['sampling_status']==status for r in sampled)
                                        for status in sorted({r['sampling_status'] for r in sampled})},
                observed_spread_range=None if not ranges else [min(ranges),max(ranges)],
                bands_with_spread=sum(v>0 for v in ranges),resolution_adequate=measurements[0]['resolution_adequate']=='True',
                basin_conclusion_eligible=measurements[0]['basin_conclusion_eligible']=='True',
                P0_grid=float(measurements[0]['P0_grid']),P0_cont=float(measurements[0]['P0_cont']),
                solver_wall_range=[min(float(r['wall_s']) for r in measurements),max(float(r['wall_s']) for r in measurements)])
            summaries[instance+'-'+mode]=summary
            if mode=='hoeffding' and len(ranges)!=10: failures.append(f'{instance}: {len(ranges)}/10 requested multiplicity bands available')
        report['checks']['measurements']=summaries
        study=json.loads(Path('docs/coverage-study-v1.8.3.json').read_text(encoding='utf8'))
        assert study['total']==2000 and study['seed_start']==10000 and study['seed_end']==11999
        assert not study['modes']['oracle']['simultaneous_guarantee'] and study['modes']['hoeffding']['simultaneous_guarantee']
        report['checks']['coverage']=study
        archive=Path('docs/archive/v1.7');manifest=json.loads((archive/'manifest.json').read_text(encoding='utf8'))
        for entry in manifest:
            assert sha256((archive/entry['archived']).read_bytes()).hexdigest()==entry['sha256']
            if entry['source'].startswith('results/'):
                assert sha256(Path(entry['source']).read_bytes()).hexdigest()==entry['sha256']
        report['checks']['archive']=dict(files=len(manifest),all_archived_hashes_verified=True,original_results_unchanged=True)
        assert source_digest()==report['source_digest'],'implementation changed during gate'
        report['failed_requirements']=failures;report['status']='FAIL' if failures else 'PASS'
        report['completed_at']=datetime.now(timezone.utc).isoformat();save();print(json.dumps(report),flush=True)
    except Exception as error:
        report['status']='FAIL';report['error']=str(error);report['completed_at']=datetime.now(timezone.utc).isoformat();save();raise
    return report


if __name__=='__main__':
    assert os.environ.get('CERTMORSE_PVPYTHON') and os.environ.get('CERTMORSE_TSFM_PYTHON'),'run scripts/stage1-gate.ps1'
    result=run()
    if result['status']!='PASS': sys.exit(1)
