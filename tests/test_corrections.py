import numpy as np
from certmorse.complex import TorusComplex,lower_star_gradient
from certmorse.forman import witness,NegativeCycle
from certmorse.scaling import cell_band,model_band
from certmorse.mip.compression import compress_bounds
from scripts.agreement import passed


def test_agreement_requires_every_proven_optimum():
    methods={m:dict(status='OPTIMAL',kappa_opt=4) for m in ['cpsatA','highsA','cpsatB']}
    assert passed(dict(methods=methods))
    for status in ['FEASIBLE','CUT_LIMIT','NO_SOLUTION','NUMERIC_INVALID']:
        changed={**methods,'cpsatB':dict(status=status,kappa_opt=None)}
        assert not passed(dict(methods=changed))
    assert not passed(dict(methods={'cpsatA':methods['cpsatA']}))
    assert not passed(dict(methods={**methods,'highsA':dict(status='OPTIMAL',kappa_opt=6)}))


def test_compression_preserves_large_gap_and_tight_band_feasibility():
    rng=np.random.default_rng(1701);cx=TorusComplex(4)
    outcomes=set()
    for k in range(100):
        g=rng.integers(-100000,100000,cx.nv)
        lo,hi=cell_band(*model_band(g-rng.integers(1,10000,cx.nv),g+rng.integers(1,10000,cx.nv),1),cx)
        a,b=lower_star_gradient(g if k%2 else rng.normal(size=cx.nv),cx)
        clo,chi=compress_bounds(lo,hi)
        assert clo.min()==0 and chi.max()<=cx.nc*(2*cx.nc-1)
        before=isinstance(witness(a,b,lo,hi,cx),NegativeCycle)
        after=isinstance(witness(a,b,clo,chi,cx),NegativeCycle)
        assert before==after
        outcomes.add(before)
    assert outcomes=={False,True}
