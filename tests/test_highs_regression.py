import numpy as np
import pytest
import highspy
from certmorse.complex import TorusComplex,lower_star_gradient
from certmorse.forman import witness
from certmorse.scaling import choose_scale,model_band,cell_band
from certmorse.mip import build_A,solve
from certmorse.mip.solvers import emit_highs


@pytest.mark.parametrize('m,seed',[(3,2300),(3,2326),(3,2327),(4,2325),(4,2330),(4,2334),(8,2308),(8,2309),(8,2319)])
@pytest.mark.parametrize('use_hint',[False,True])
def test_highs_historical_disagreements(m,seed,use_hint,tmp_path):
    rng=np.random.default_rng(seed)
    cx=TorusComplex(m)
    g=rng.normal(size=cx.nv)
    width=rng.uniform(.01,.5,size=cx.nv)
    scale,_=choose_scale(g-width,g+width)
    lo,hi=cell_band(*model_band(g-width,g+width,scale),cx)
    model=build_A(lo,hi,cx)
    a,b=lower_star_gradient(g,cx)
    hint=dict(x=witness(a,b,lo,hi,cx),y=np.concatenate((a,b))) if use_hint else None
    cp=solve(model,'cpsat',30,8,hint,str(tmp_path/'cp.log'))
    hi=solve(model,'highs',30,8,hint,str(tmp_path/'hi.log'))
    assert cp.status==hi.status=='OPTIMAL'
    assert cp.kappa_opt==hi.kappa_opt
    assert cp.kappa_lb<=cp.kappa_incumbent and hi.kappa_lb<=hi.kappa_incumbent
    assert cp.lb_is_certificate and not hi.lb_is_certificate
    # Reimported MPS must accept the independently constructed integer witness.
    h=highspy.Highs();h.setOptionValue('output_flag',False)
    assert h.readModel(str(tmp_path/'hi.mps'))==highspy.HighsStatus.kOk
    from certmorse.mip.compression import compress_bounds
    clo,chi=compress_bounds(lo,model.cell_hi)
    ca,cb=cx.split_matching(cp.y)
    values=np.concatenate((witness(ca,cb,clo,chi,cx),cp.y))
    lp=h.getLp()
    assert lp.sense_==highspy.ObjSense.kMaximize
    assert all(i==highspy.HighsVarType.kContinuous for i in lp.integrality_[:cx.nc])
    assert all(i==highspy.HighsVarType.kInteger for i in lp.integrality_[cx.nc:])
    assert all(lo<=v<=hi for lo,v,hi in zip(lp.col_lower_,values,lp.col_upper_))
    for row in range(lp.num_row_):
        _,indices,coefs=h.getRowEntries(row)
        activity=sum(int(c)*int(values[i]) for i,c in zip(indices,coefs))
        assert lp.row_lower_[row]<=activity<=lp.row_upper_[row]
