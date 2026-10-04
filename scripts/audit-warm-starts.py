import csv
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from certmorse.complex import TorusComplex
from certmorse.mip.warm_start import simplified_hint
from certmorse.complex import lower_star_gradient

cx=TorusComplex(16)
records=[]
output=Path('results/corrections/warm-start-audit');output.mkdir(parents=True,exist_ok=True)
for path in sorted(Path('results/stage1-r8a').glob('*/measurement.json')):
    row=json.loads(path.read_text())
    data=np.load(path.parent/'matching.npz')
    delta=float(np.min((data['cell_hi'][:cx.nv]-data['cell_lo'][:cx.nv])/(2*row['scale'])))
    hint,status=simplified_hint(path.parent/'band.vtu',output/(path.parent.name+'.csv'),2*delta,data['cell_lo'],data['cell_hi'],cx)
    kappa=None if hint is None else cx.nc-2*int(hint['y'].sum())
    raw=np.loadtxt(output/(path.parent.name+'.csv'),delimiter=',',skiprows=1)[:,0]
    a,b=lower_star_gradient(raw,cx)
    records.append(dict(seed=row['seed'],status=status,kappa=kappa,scalar_only_kappa=cx.nc-2*int(a.sum()+b.sum()),UB_pers=row['UB_pers'],UB_witness_justified=bool(hint is not None and kappa<=row['UB_pers'])))
    print(records[-1],flush=True)
with open('docs/warm-start-audit-v1.7.csv','w',newline='',encoding='utf8') as stream:
    writer=csv.DictWriter(stream,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
