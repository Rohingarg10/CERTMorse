"""Amended T32; keep the original failing run/definition as historical evidence."""
import csv
import json
from pathlib import Path
import numpy as np
import pytest
from certmorse.complex import TorusComplex,lower_star_gradient,basins
from certmorse.forman import witness,NegativeCycle
from certmorse.instances import load_instance
from certmorse.landscape import exact_landscape
from certmorse.metrics import basin_probability
from certmorse.scaling import choose_scale,model_band,cell_band
from certmorse.mip import build_A,solve,sample_optima
from certmorse.mip.bounds import truth_count,ZERO_SCALE
from certmorse.rng import streams

NARROW_HALF_WIDTH = 0.01  # v1.6 T23/T26, retained for the T32 narrow band.
TIME_LIMIT_S = 600  # v1.6 section 6.4.
SAMPLING_CAP_S = 300  # D14.4(b).
MAX_OPTIMA = 20  # D14.4(b).
THREADS = 8  # v1.6 section 6.4.


def old_exact_global_control(y,lower,upper,cx):
    labels=basins(cx.split_matching(y)[0],cx)
    selected=[root for root in np.unique(labels) if lower.ravel()[labels==root].min()<=upper.min()]
    return float(np.mean(np.isin(labels,selected)))


def test_T32_preserved_counterexample_corrected():
    cx=TorusComplex(16)
    with np.load('docs/t32-counterexample-v1.8.1.npz') as z:
        P,possible=basin_probability(z['y'],z['mean'],load_instance('R8a').W,cx,z['lower'],z['upper'])
        assert P==possible==1
        assert old_exact_global_control(z['y'],z['lower'],z['upper'],cx)==0.5234375


def test_T32_archived_optima_depth_regression():
    cx=TorusComplex(16);W=load_instance('R8a').W;values=[];old_values=[]
    archive=Path('docs/archive/v1.7')
    with (archive/'stage1-r8a-v1.7-oracle.csv').open(newline='') as stream:
        rows=list(csv.DictReader(stream))
    for row in rows:
        with np.load(archive/'results/stage1-r8a-v1.7-oracle'/row['run_id']/'matching.npz') as z:
            for y in z['optima']:
                P,possible=basin_probability(y,z['mean'],W,cx,z['lower'],z['upper'])
                assert P==1 and P<=possible
                labels=basins(cx.split_matching(y)[0],cx);roots=np.unique(labels);field=z['mean'].ravel()
                selected=roots[field[roots]<=field[roots].min()+0.02*W]
                old_values.append(float(np.mean(np.isin(labels,selected))));values.append(P)
    assert len(values)==200 and min(old_values)==0.27734375


def test_T32_narrow_R8a_sampled_optima(tmp_path):
    inst=load_instance('R8a');cx=TorusComplex(16)
    field,_,_=exact_landscape(inst,16,'a',7)
    lower,upper=field-NARROW_HALF_WIDTH,field+NARROW_HALF_WIDTH
    scale,_=choose_scale(lower,upper);lo,hi=cell_band(*model_band(lower,upper,scale),cx)
    a,b=lower_star_gradient(field,cx);x=witness(a,b,lo,hi,cx)
    assert not isinstance(x,NegativeCycle)
    model=build_A(lo,hi,cx)
    result=solve(model,'cpsat',TIME_LIMIT_S,THREADS,dict(x=x,y=np.concatenate((a,b))),str(tmp_path/'solve.log'))
    assert result.status=='OPTIMAL'
    samples,status=sample_optima(model,result.kappa_opt,MAX_OPTIMA,SAMPLING_CAP_S,streams(32)['fc'],
                                 initial_result=result,log_path=str(tmp_path/'sample.log'))
    assert samples
    for sample in samples:
        P,possible=basin_probability(sample.y,field,inst.W,cx,lower,upper)
        assert P==1 and P<=possible
    target=Path('results/stage1-v1.8.3-tests/T32');target.mkdir(parents=True,exist_ok=True)
    (target/'narrow-sampling.json').write_text(json.dumps(dict(status=status,optima=len(samples),P=1)),encoding='utf-8', newline='\n')


@pytest.mark.parametrize('side',['lower','upper'])
def test_T32_depth_field_outside_reported_band_raises(side):
    z=np.load('docs/t32-counterexample-v1.8.1.npz');lo=z['lower'].copy();hi=z['upper'].copy()
    if side=='lower': lo.flat[0]=z['mean'].flat[0]+1
    else: hi.flat[0]=z['mean'].flat[0]-1
    with pytest.raises(AssertionError,match='outside the reported band'):
        basin_probability(z['y'],z['mean'],12,TorusComplex(16),lo,hi)


def test_kappa_zero_uses_fixed_scale(tmp_path):
    cx=TorusComplex(3)
    result=truth_count(np.zeros(cx.nv),cx,1,str(tmp_path/'zero.log'))
    assert result['ties_exact']==cx.ne and result['kappa_true'] is None
    assert result['kappa_zero']==4 and result['kappa_zero_scale']==ZERO_SCALE==10**6
