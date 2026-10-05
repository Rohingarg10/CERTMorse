"""T31 validity and critical cells, with independently solved random bands."""
import json
from pathlib import Path
import numpy as np
from certmorse.complex import TorusComplex,lower_star_gradient
from certmorse.forman import witness,NegativeCycle,is_discrete_morse
from certmorse.scaling import choose_scale,model_band,cell_band
from certmorse.mip import build_A,solve
from certmorse.mip.regions import region_bound

T31_BANDS = 50  # v1.8 T31.
TIME_LIMIT_S = 600  # Retained solver protocol.
THREADS = 8  # Retained solver protocol.


def test_T31_region_bound_on_50_optimal_random_bands():
    cx=TorusComplex(4);records=[]
    output=Path('results/stage1-v1.8.3-tests/T31');output.mkdir(parents=True,exist_ok=True)
    for seed in range(T31_BANDS):
        rng=np.random.default_rng(3100+seed)
        field=rng.normal(size=cx.nv);width=rng.uniform(.01,.5,cx.nv)
        scale,_=choose_scale(field-width,field+width)
        lo,hi=cell_band(*model_band(field-width,field+width,scale),cx)
        regions=region_bound(lo,hi,cx)
        a,b=lower_star_gradient(field,cx);x=witness(a,b,lo,hi,cx)
        assert not isinstance(x,NegativeCycle)
        # Solve without the proposed bound rows so the validity comparison
        # does not rely on the very inequalities being tested.
        result=solve(build_A(lo,hi,cx,valid_rows=False),'cpsat',TIME_LIMIT_S,THREADS,
                     dict(x=x,y=np.concatenate((a,b)),seed=seed),str(output/f'{seed:02d}.log'))
        assert result.status=='OPTIMAL', (seed,result.status)
        aa,bb=cx.split_matching(result.y)
        assert is_discrete_morse(result.x,aa,bb,cx)[0]
        assert regions.LB_region<=result.kappa_opt
        used=np.bincount(cx.pairs[result.y.astype(bool)].ravel(),minlength=cx.nc)>0
        for family in (regions.minimum_regions,regions.maximum_regions):
            seen=set()
            for region in family:
                assert seen.isdisjoint(region);seen.update(region)
                assert any(not used[c] for c in region)
        records.append(dict(seed=seed,kappa_opt=result.kappa_opt,LB_region=regions.LB_region,
                            equality=result.kappa_opt==regions.LB_region))
        np.savez_compressed(output/f'{seed:02d}.npz',lo=lo,hi=hi,y=result.y,x=result.x)
    report=dict(optimal_bands=len(records),valid_rows_used=False,equal=sum(r['equality'] for r in records),
                equality_rate=sum(r['equality'] for r in records)/len(records),bands=records)
    Path('docs/T31-v1.8.3.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8', newline='\n')
