import numpy as np
from certmorse.landscape import execute_run, run
from certmorse.runid import default_config


def test_T1_rerun_npz(tmp_path):
    cfg=default_config(dict(experiment='stage1-landscape',grid_m=16,noise='a',seed=7))
    output=execute_run(cfg,root=tmp_path)
    rerun=output.with_name(output.name+'.rerun')
    run(cfg,rerun)
    with np.load(output/'landscape.npz') as a,np.load(rerun/'landscape.npz') as b:
        assert set(a.files)==set(b.files)
        for field in a.files:
            if a[field].dtype.kind in 'US': assert np.array_equal(a[field],b[field])
            else: np.testing.assert_allclose(a[field],b[field],atol=1e-12,rtol=0)
    assert execute_run(cfg,root=tmp_path,resume=True)==output
