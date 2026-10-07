"""Simulation-only grid adequacy table; see docs/METHOD.md."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from certmorse.instances import load_instance
from certmorse.landscape import exact_landscape,measured_symmetry,field_diagnostics
from certmorse.complex import TorusComplex
from certmorse.resolution import resolution_check,GRID_SIZES,RESOLUTION_INSTANCES
from certmorse.runid import prepare_run
from certmorse.stage1 import complete
from certmorse.provenance import source_digest


def run(resume=True):
    saved=Path('docs/resolution-v1.8.3.json')
    if saved.exists():
        report=json.loads(saved.read_text(encoding='utf-8'))
        assert len(report['rows'])==20
        assert all((Path(row['run_path'])/'field.npz').is_file() for row in report['rows'])
        return report
    raise RuntimeError('saved resolution evidence is missing; completed outputs are read-only')


def historical_run(resume=False):
    rows=[]
    for name in RESOLUTION_INSTANCES:
        for m in GRID_SIZES:
            cfg=dict(experiment='stage1-resolution-v1.8.3',instance=name,grid_m=m,seed=1003)
            path,needed=prepare_run(cfg,resume=resume)
            if needed:
                inst=load_instance(name);field,_,_=exact_landscape(inst,m,'a',1003)
                result=resolution_check(inst,field,'a',1003)
                result.update(instance=name,grid_m=m,noise='a',run_path=str(path.relative_to(Path.cwd())),
                              **measured_symmetry(inst,'a',1003),**field_diagnostics(field,TorusComplex(m)))
                np.savez_compressed(path/'field.npz',truth=field,metadata=json.dumps(result))
                (path/'measurement.json').write_text(json.dumps(result,indent=2),encoding='utf-8', newline='\n')
                complete(path)
            else: result=json.loads((path/'measurement.json').read_text(encoding='utf8'))
            rows.append(result)
            print(json.dumps({k:result[k] for k in ('instance','grid_m','resolution_adequate','worst_grid_depth_error',
                                                   'P0_grid','P0_cont','RQ2_informative')}),flush=True)
    selected={name:next((r['grid_m'] for r in rows if r['instance']==name and r['resolution_adequate']),None)
              for name in RESOLUTION_INSTANCES}
    report=dict(method='docs/METHOD.md',source_digest=source_digest(),rows=rows,
                smallest_passing_grid=selected,p2_fallback=not any(r['RQ2_informative'] for r in rows))
    Path('docs/resolution-v1.8.3.json').write_text(json.dumps(report,indent=2),encoding='utf-8', newline='\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--resume',action='store_true');run(p.parse_args().resume)
