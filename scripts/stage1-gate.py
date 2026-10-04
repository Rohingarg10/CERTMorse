"""One executable Stage 1 gate, including the large checks outside pytest."""
import csv
from datetime import datetime, timezone
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
from certmorse.metrics import basin_probability
from certmorse.instances import load_instance
from certmorse.provenance import source_digest
from scripts.agreement import passed


def run():
    output=Path('results/corrections/gate')/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ');output.mkdir(parents=True,exist_ok=True)
    report=dict(specification='v1.7',source_digest=source_digest(),status='RUNNING',steps=[],checks={})
    destination=Path('docs/stage1-gate.json')
    def save(): destination.write_text(json.dumps(report,indent=2),encoding='utf8')
    save()
    commands=[('tests',[sys.executable,'-m','pytest','-q','--junitxml='+str(output/'tests.xml')]),
              ('agreement',[sys.executable,'scripts/agreement.py','--resume']),
              ('r8a',[sys.executable,'-m','certmorse.stage1','--resume']),
              ('coverage',[sys.executable,'scripts/coverage-study.py'])]
    try:
        for name,command in commands:
            print(f'Running {name}',flush=True);start=time.perf_counter()
            with (output/(name+'.log')).open('w',encoding='utf8') as stream:
                result=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT)
            report['steps'].append(dict(name=name,exit_code=result.returncode,wall_s=time.perf_counter()-start,log=str(output/(name+'.log'))));save()
            if result.returncode: raise AssertionError(f'{name} failed; see {output/(name+".log")}')
        cases=ET.parse(output/'tests.xml').findall('.//testcase')
        assert cases and not any(c.find('skipped') is not None for c in cases),'required integration checks must not be skipped'
        report['checks']['tests']=dict(passed=len(cases),skipped=0)
        rows=json.loads(Path('docs/agreement-v1.7.json').read_text())
        assert {(r['m'],r['seed']) for r in rows}=={(m,s) for m in [3,4,8] for s in range(20 if m==8 else 50)}
        assert len(rows)==120 and all(passed(r) for r in rows)
        for row in rows:
            cx=TorusComplex(row['m'])
            for record in row['methods'].values():
                path=Path(record['run_path'])
                assert yaml.safe_load((path/'config.yaml').read_text())['source_digest']==report['source_digest']
                assert json.loads((path/'status.json').read_text())['complete']
                data=np.load(path/'solution.npz')
                a,b=cx.split_matching(data['y'])
                assert is_discrete_morse(data['x'],a,b,cx)[0]
                assert np.all((data['lo']<=data['x'])&(data['x']<=data['hi']))
                assert cx.nc-2*int(data['y'].sum())==record['kappa_opt']
        report['checks']['agreement']=dict(bands=120,optimal_solvers=360,exact_witnesses_verified=360)
        with Path('docs/stage1-r8a-v1.7-oracle.csv').open(newline='') as stream: measurements=list(csv.DictReader(stream))
        assert len(measurements)==20 and {int(r['seed']) for r in measurements}==set(range(20))
        cx=TorusComplex(16);inst=load_instance('R8a');ranges=[]
        for row in measurements:
            path=Path('results/stage1-r8a-v1.7-oracle')/row['run_id']
            assert yaml.safe_load((path/'config.yaml').read_text())['source_digest']==report['source_digest']
            assert row['status']=='OPTIMAL' and row['UB_witness_justified']=='True'
            assert int(row['LB_mand'])<=int(row['kappa_opt'])<=int(row['UB_pers'])
            assert row['warm_start_used']=='ttk_simplified' and row['ttk_warm_status']=='accepted'
            data=np.load(path/'matching.npz')
            a,b=cx.split_matching(data['y'])
            assert is_discrete_morse(data['x'],a,b,cx)[0]
            assert np.all((data['cell_lo']<=data['x'])&(data['x']<=data['cell_hi']))
            ta,tb=lower_star_gradient(data['truth'],cx)
            transfer=not isinstance(witness(ta,tb,data['cell_lo'],data['cell_hi'],cx),NegativeCycle)
            covered=bool(np.all((data['lower']<=data['truth'])&(data['truth']<=data['upper'])))
            assert (row['transfer_claim']=='True')==(covered and transfer)
            if int(row['seed'])<10:
                optima=data['optima'];assert len(optima)==int(row['n_opt_found']) and len(optima)>=2
                assert len(np.unique(optima[:,:len(cx.pairs_ve)],axis=0))==len(optima)
                values=[]
                for y in optima:
                    aa,bb=cx.split_matching(y)
                    assert cx.nc-2*int(y.sum())==int(row['kappa_opt'])
                    assert not isinstance(witness(aa,bb,data['cell_lo'],data['cell_hi'],cx),NegativeCycle)
                    values.append(basin_probability(y,data['mean'],inst.W,cx))
                np.testing.assert_allclose([min(values),np.median(values),max(values)],[float(row[k]) for k in ['P_lo','P_med','P_hi']])
                ranges.append(max(values)-min(values))
        report['checks']['r8a']=dict(optimal_bands=20,warm_starts_justified=20,multiplicity_bands=len(ranges),observed_spread_range=[min(ranges),max(ranges)])
        study=json.loads(Path('docs/coverage-study-v1.7.json').read_text())
        assert study['total']==2000 and study['seed_start']==10000
        assert not study['modes']['oracle']['simultaneous_guarantee'] and study['modes']['hoeffding']['simultaneous_guarantee']
        report['checks']['coverage']=study['modes']
        assert source_digest()==report['source_digest'],'implementation changed during gate'
        report['status']='PASS';save();print(json.dumps(report),flush=True)
    except Exception as error:
        report['status']='FAIL';report['error']=str(error);save();raise
    return report


if __name__=='__main__':
    assert os.environ.get('CERTMORSE_PVPYTHON') and os.environ.get('CERTMORSE_TSFM_PYTHON'),'run scripts/stage1-gate.ps1'
    run()
