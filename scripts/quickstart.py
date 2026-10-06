"""Solve and independently verify one small synthetic band; no saved unit is used."""
import argparse
import json
from pathlib import Path
import platform
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from certmorse.complex import TorusComplex,lower_star_gradient
from certmorse.forman import witness,NegativeCycle,is_discrete_morse
from certmorse.mip import build_A,solve
from certmorse.metrics import critical_counts
from certmorse.provenance import source_digest
from certmorse.scaling import choose_scale,model_band,cell_band


def run(output):
    output=Path(output)
    if output.is_absolute():
        raise ValueError('Use a repository-relative output directory')
    output.mkdir(parents=True,exist_ok=True)
    started=time.perf_counter()
    cx=TorusComplex(3);v=np.arange(cx.nv)
    field=np.cos(2*np.pi*(v%3+.25)/3)+.7*np.cos(2*np.pi*(v//3+.125)/3)
    lower,upper=field-.01,field+.01
    scale,_=choose_scale(lower,upper)
    lo,hi=cell_band(*model_band(lower,upper,scale),cx)
    a,b=lower_star_gradient(field,cx);x=witness(a,b,lo,hi,cx)
    assert not isinstance(x,NegativeCycle)
    result=solve(build_A(lo,hi,cx),'cpsat',60,1,dict(x=x,y=np.concatenate((a,b)),seed=0),str(output/'solve.log'))
    assert result.status=='OPTIMAL' and result.kappa_opt==4,(result.status,result.kappa_opt)
    a,b=cx.split_matching(result.y);checked=witness(a,b,lo,hi,cx)
    assert not isinstance(checked,NegativeCycle)
    assert is_discrete_morse(checked,a,b,cx)[0]
    assert np.all((lo<=checked)&(checked<=hi))
    elapsed=time.perf_counter()-started
    assert elapsed<300,elapsed
    report=dict(status='OPTIMAL',kappa_star=result.kappa_opt,kappa_lb=result.kappa_lb,
        critical_counts=list(map(int,critical_counts(result.y,cx))),grid_m=3,cells=cx.nc,
        exact_witness_valid=True,wall_s=elapsed,source_digest=source_digest(),
        solve_cap_s=60,workers=1,seed=0,hardware=dict(python=platform.python_version(),system=platform.system(),
        processor=platform.processor(),machine=platform.machine()),report=(output/'report.json').as_posix())
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(report))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='results/quickstart')
    run(parser.parse_args().out)
