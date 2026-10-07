"""T31 validity and critical cells, with independently solved random bands."""
import json
from pathlib import Path
import numpy as np
from certmorse.complex import TorusComplex,lower_star_gradient
from certmorse.forman import witness,NegativeCycle,is_discrete_morse
from certmorse.scaling import choose_scale,model_band,cell_band
from certmorse.mip import build_A,solve
from certmorse.mip.regions import region_bound

T31_BANDS = 50  # Saved random-band cases per grid size.
TIME_LIMIT_S = 600  # Retained solver protocol.
THREADS = 8  # Retained solver protocol.


def test_T31_region_bound_on_50_optimal_random_bands():
    cx=TorusComplex(4);records=[]
    output=Path('results/stage1-v1.8.3-tests/T31')
    saved=json.loads(Path('docs/T31-v1.8.3.json').read_text(encoding='utf-8'))
    assert saved['optimal_bands']==50 and not saved['valid_rows_used']
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
        assert 'status: OPTIMAL' in (output/f'{seed:02d}.log').read_text(encoding='utf-8')
        with np.load(output/f'{seed:02d}.npz') as data:
            assert np.array_equal(lo,data['lo']) and np.array_equal(hi,data['hi'])
            y=data['y'];xx=data['x']
        optimum=cx.nc-2*int(y.sum())
        assert saved['bands'][seed]['kappa_opt']==optimum
        aa,bb=cx.split_matching(y)
        assert not isinstance(witness(aa,bb,lo,hi,cx),NegativeCycle)
        assert is_discrete_morse(xx,aa,bb,cx)[0]
        assert regions.LB_region<=optimum
        used=np.bincount(cx.pairs[y.astype(bool)].ravel(),minlength=cx.nc)>0
        for family in (regions.minimum_regions,regions.maximum_regions):
            seen=set()
            for region in family:
                assert seen.isdisjoint(region);seen.update(region)
                assert any(not used[c] for c in region)
        records.append(dict(seed=seed,kappa_opt=optimum,LB_region=regions.LB_region,
                            equality=optimum==regions.LB_region))
    report=dict(optimal_bands=len(records),valid_rows_used=False,equal=sum(r['equality'] for r in records),
                equality_rate=sum(r['equality'] for r in records)/len(records),bands=records)
    assert report==saved
