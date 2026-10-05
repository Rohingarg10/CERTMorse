"""Fill ten sampling slots from eligible prescribed bands, without re-solving counts.

The primary driver attempts the first ten seeds. If any is non-optimal, take
the next OPTIMAL seed among the same twenty bands. This changes neither the
count solves nor the per-band sampling procedure or budget.
"""
import csv
from datetime import datetime,timezone
from hashlib import sha256
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import yaml
from certmorse.complex import TorusComplex
from certmorse.forman import is_discrete_morse
from certmorse.instances import load_instance
from certmorse.metrics import basin_probability
from certmorse.mip import build_A
from certmorse.mip.milp import SolveResult
from certmorse.mip.solvers import sample_optima
from certmorse.provenance import source_digest
from certmorse.rng import streams
from certmorse.runid import prepare_run
from certmorse.stage1 import MAX_OPTIMA,SAMPLING_CAP_S,GRID_M,SHOTS,ALPHA,complete

SAMPLING_BANDS = 10  # v1.8 gate item 4.
INSTANCES = ('R8a','E8a','W8a')  # v1.8 Stage 1 scope.


def run():
    saved=Path('docs/multiplicity-completion-v1.8.3.json')
    previous=json.loads(saved.read_text(encoding='utf8')) if saved.exists() else {}
    if previous.get('source_digest')!=source_digest(): previous={}
    report=dict(source_digest=source_digest(),selection='first ten OPTIMAL bands in seed order',
                driver_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),instances={})
    for name in INSTANCES:
        destination=Path(f'docs/stage1-{name.lower()}-v1.8.3-hoeffding.csv')
        with destination.open(newline='',encoding='utf8') as stream:
            rows=list(csv.DictReader(stream))
        completed=sum(int(r['n_opt_found'])>0 for r in rows)
        supplemental=list(previous.get('instances',{}).get(name,{}).get('supplemental',[]))
        for row in sorted(rows,key=lambda r:int(r['seed'])):
            if completed>=SAMPLING_BANDS: break
            if row['status']!='OPTIMAL' or int(row['n_opt_found']): continue
            primary=Path(f'results/stage1-{name.lower()}-v1.8.3-hoeffding')/row['run_id']
            cfg=yaml.safe_load((primary/'config.yaml').read_text(encoding='utf8'))
            assert cfg['source_digest']==source_digest()
            assert cfg['solver']=='cpsat' and row['lb_is_certificate']=='True'
            assert 'status: OPTIMAL' in (primary/'solver.log').read_text(encoding='utf8')
            assert json.loads((primary/'status.json').read_text(encoding='utf8'))['complete']
            with np.load(primary/'matching.npz') as data: arrays={key:data[key] for key in data.files}
            cx=TorusComplex(GRID_M);inst=load_instance(name);a,b=cx.split_matching(arrays['y'])
            assert is_discrete_morse(arrays['x'],a,b,cx)[0]
            assert cx.nc-2*int(arrays['y'].sum())==int(row['kappa_opt'])
            # Rehydrate the actually logged OPTIMAL primary result. There is
            # no new count solve and no claim of optimality from sampling.
            initial=SolveResult(status='OPTIMAL',kappa_incumbent=int(row['kappa_incumbent']),
                kappa_lb=int(row['kappa_lb']),kappa_opt=int(row['kappa_opt']),lb_is_certificate=True,
                bound=float(row['bound']),gap=float(row['gap']),wall_s=float(row['wall_s']),
                nodes=int(row['nodes']),x=arrays['x'],y=arrays['y'])
            sampling_cfg=dict(experiment='stage1-multiplicity-v1.8.3-'+row['run_id'],instance=name,
                grid_m=GRID_M,shots=SHOTS,alpha=ALPHA,band_mode='hoeffding',seed=int(row['seed']),
                multiplicity={'enabled':True,'max_optima':MAX_OPTIMA,'time_cap_s':SAMPLING_CAP_S})
            path,needed=prepare_run(sampling_cfg,resume=True)
            if needed:
                model=build_A(arrays['cell_lo'],arrays['cell_hi'],cx)
                samples,status=sample_optima(model,initial.kappa_opt,MAX_OPTIMA,SAMPLING_CAP_S,
                    streams(int(row['seed']))['fc'],initial_result=initial,log_path=str(path/'sampling.log'))
                values=[basin_probability(s.y,arrays['mean'],inst.W,cx,arrays['lower'],arrays['upper']) for s in samples]
                np.savez_compressed(path/'samples.npz',optima=np.array([s.y for s in samples],dtype=np.int8),
                    sample_P=np.array([v[0] for v in values]),sample_P_possible=np.array([v[1] for v in values]))
                record=dict(primary_run_path=str(primary),n_opt_found=len(samples),sampling_status=status,
                    P_med=float(np.median([v[0] for v in values])),P_lo=min(v[0] for v in values),P_hi=max(v[0] for v in values),
                    completed_at=datetime.now(timezone.utc).isoformat(),driver_sha256=report['driver_sha256'])
                (path/'measurement.json').write_text(json.dumps(record,indent=2),encoding='utf8')
                if name=='R8a': assert all(v[0]==1 for v in values),'T32 supplemental R8a control failed; artifact preserved'
                complete(path)
            else: record=json.loads((path/'measurement.json').read_text(encoding='utf8'))
            with np.load(path/'samples.npz') as samples:
                for key in samples.files: arrays[key]=samples[key]
            np.savez_compressed(primary/'matching.npz',**arrays)
            measurement=json.loads((primary/'measurement.json').read_text(encoding='utf8'))
            for key in ('n_opt_found','sampling_status','P_med','P_lo','P_hi'): measurement[key]=record[key]
            measurement['multiplicity_run_path']=str(path.relative_to(Path.cwd()))
            (primary/'measurement.json').write_text(json.dumps(measurement,indent=2),encoding='utf8')
            for key in ('n_opt_found','sampling_status','P_med','P_lo','P_hi','multiplicity_run_path'): row[key]=measurement[key]
            completed+=1;supplemental.append(dict(instance=name,seed=int(row['seed']),run_path=measurement['multiplicity_run_path'],**record))
            print(json.dumps(supplemental[-1]),flush=True)
        # Every row has the optional provenance key, including resumed rows.
        for row in rows:
            row.setdefault('multiplicity_run_path','')
            primary=Path(f'results/stage1-{name.lower()}-v1.8.3-hoeffding')/row['run_id']
            measurement=json.loads((primary/'measurement.json').read_text(encoding='utf8'))
            measurement.setdefault('multiplicity_run_path','')
            (primary/'measurement.json').write_text(json.dumps(measurement,indent=2),encoding='utf8')
        with destination.open('w',newline='',encoding='utf8') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
        report['instances'][name]=dict(sampled_bands=completed,supplemental=supplemental,
                                      optimal_available=sum(r['status']=='OPTIMAL' for r in rows))
        Path('docs/multiplicity-completion-v1.8.3.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    return report


if __name__=='__main__': run()
