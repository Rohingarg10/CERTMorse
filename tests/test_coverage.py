import json
from pathlib import Path
import numpy as np
from scipy.special import ndtri
from certmorse.instances import load_instance, cost_values
from certmorse.landscape import exact_landscape, sample_landscape, make_band


def test_T3_oracle_200_seeds():
    inst=load_instance('R8a')
    truth,var,probs=exact_landscape(inst,16,'a',1003)
    z=float(ndtri(1-.05/(2*256)))
    flags=[]
    for seed in range(200):
        mean,sample_var=sample_landscape((probs,cost_values(inst)),1000,np.random.default_rng(seed))
        lo,hi=make_band(mean,var,sample_var,1000,inst.W,.05,'oracle')
        flags.append(bool(np.all((lo<=truth)&(truth<=hi))))
        half=np.maximum(z*np.sqrt(var/1000),1e-4*inst.W)
        np.testing.assert_allclose(lo,np.maximum(mean-half,-inst.W),atol=1e-12)
        np.testing.assert_allclose(hi,np.minimum(mean+half,0),atol=1e-12)
    report=dict(seeds=list(range(200)),coverage=float(np.mean(flags)),covered=sum(flags),total=200,z=z,formula_verified=True)
    path=Path('results/corrections/legacy-coverage-recheck.json');path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,indent=2),encoding='utf8')
    assert report['coverage']>=.93, report
