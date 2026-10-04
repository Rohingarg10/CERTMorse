import numpy as np
import pytest
from scipy.optimize import linprog
from certmorse.complex import TorusComplex, lower_star_gradient, basins
from certmorse.forman import witness, witness_range, NegativeCycle, is_discrete_morse, difference_arcs
from certmorse.scaling import choose_scale, model_band, cell_band
from certmorse.persistence import persistence, lower_star_values, bottleneck
from certmorse.mip import build_A, solve, solve_B_lazy
from certmorse.mip.bounds import persistence_count


def field(cx, frequency=1):
    v=np.arange(cx.nv)
    return np.cos(frequency*2*np.pi*(v%cx.m)/cx.m)+np.cos(2*np.pi*(v//cx.m)/cx.m)-2.5


def bounds(g,cx,width=.01):
    s,_=choose_scale(g-width,g+width)
    a,b=model_band(g-width,g+width,s)
    return (*cell_band(a,b,cx),s)


@pytest.mark.parametrize('m',[3,4,8,16])
def test_T4_incidence(m):
    cx=TorusComplex(m)
    assert len(set(tuple(sorted(e)) for e in cx.edge_vertices))==3*m*m
    assert len(set(tuple(sorted(t)) for t in cx.tri_vertices))==2*m*m
    assert all(len(cx.cofaces[v])==6 for v in range(cx.nv))
    assert all(len(cx.cofaces[e])==2 for e in range(cx.nv,4*cx.nv))
    assert cx.nv-cx.ne+cx.nt==0
    assert cx.pairs.shape==(12*m*m,2)


@pytest.mark.parametrize('frequency,expected',[(1,4),(2,8)])
def test_T5_T15_T22_lower_star(frequency,expected):
    cx=TorusComplex(16)
    g=field(cx,frequency)
    a,b=lower_star_gradient(g,cx)
    assert cx.nc-2*int(a.sum()+b.sum())==expected
    lo,hi,_=bounds(g,cx)
    x=witness(a,b,lo,hi,cx)
    assert not isinstance(x,NegativeCycle)
    assert is_discrete_morse(x,a,b,cx)==(True,{})
    labels=basins(a,cx)
    assert len(np.unique(labels))==expected//4
    if frequency==2:
        assert all(.4<=np.mean(labels==v)<=.6 for v in np.unique(labels))


def test_T15_repeated_zero_values():
    cx=TorusComplex(8)
    g=np.zeros(cx.nv)
    lo,hi,_=bounds(g,cx)
    a,b=lower_star_gradient(g,cx)
    x=witness(a,b,lo,hi,cx)
    assert not isinstance(x,NegativeCycle)
    assert is_discrete_morse(x,a,b,cx)[0]


@pytest.mark.parametrize('frequency,expected',[(1,4),(2,8)])
@pytest.mark.parametrize('backend',['cpsat','highs'])
def test_T23_T26_known_answer(frequency,expected,backend,tmp_path):
    cx=TorusComplex(16)
    lo,hi,s= bounds(field(cx,frequency),cx)
    assert s==100000
    result=solve(build_A(lo,hi,cx),backend,60,8,None,str(tmp_path/'solver.log'))
    assert result.status=='OPTIMAL'
    assert result.kappa_opt==expected
    assert result.kappa_lb==expected
    a,b=cx.split_matching(result.y)
    assert is_discrete_morse(result.x,a,b,cx)[0]
    matched=np.bincount(cx.pairs[result.y.astype(bool)].ravel(),minlength=cx.nc)>0
    assert [int(np.sum(~matched[cx.dim==d])) for d in (0,1,2)]==[expected//4,expected//2,expected//4]


def test_T24_persistence():
    cx=TorusComplex(8)
    g=field(cx,2)
    exact=persistence(lower_star_values(g,cx),cx,1)
    assert [int(np.sum(np.isinf(exact[q][:,1]))) for q in (0,1,2)]==[1,2,1]
    assert bottleneck(exact,exact)==0
    lo,hi,s=bounds(g,cx)
    a,b=lower_star_gradient(g,cx)
    x=witness(a,b,lo,hi,cx)
    diag=persistence(x,cx,s)
    finite=sum(int(np.sum(np.isfinite(d[:,1]))) for d in diag.values())
    assert 2*finite+4 <= cx.nc-2*int(a.sum()+b.sum())


def test_T16_perfect_morse_persistence_reference():
    cx=TorusComplex(16)
    diagram=persistence(lower_star_values(field(cx),cx),cx,1)
    assert [np.sum(np.isinf(diagram[q][:,1])) for q in (0,1,2)]==[1,2,1]
    for delta in (0,.01,.1,1,100): assert persistence_count(diagram,delta)==4


@pytest.mark.parametrize('backend',['cpsat','highs'])
def test_T8_backends_and_B(backend,tmp_path):
    cx=TorusComplex(3)
    lo,hi,_=bounds(field(cx),cx,.3)
    a=solve(build_A(lo,hi,cx),backend,20,8,None,str(tmp_path/f'{backend}.log'))
    b=solve_B_lazy(cx,lo,hi,'cpsat',30,8,None,str(tmp_path/'b.log'))
    assert a.status==b.status=='OPTIMAL'
    assert a.kappa_opt==b.kappa_opt


def test_T28_range_against_lp():
    cx=TorusComplex(3)
    rng=np.random.default_rng(51)
    for _ in range(3):
        g=rng.normal(size=cx.nv)
        lo,hi,_=bounds(g,cx,.3)
        a,b=lower_star_gradient(g,cx)
        rlo,rhi=witness_range(a,b,lo,hi,cx)
        y=np.concatenate((a,b))
        arcs=difference_arcs(y,lo,hi,cx)
        mat=[]; rhs=[]
        for u,v,w,_ in arcs:
            row=np.zeros(cx.nc)
            if u<cx.nc: row[u]-=1
            if v<cx.nc: row[v]+=1
            mat.append(row);rhs.append(w)
        for v in range(cx.nv):
            objective=np.zeros(cx.nc);objective[v]=1
            mn=linprog(objective,A_ub=mat,b_ub=rhs,bounds=[(None,None)]*cx.nc,method='highs')
            mx=linprog(-objective,A_ub=mat,b_ub=rhs,bounds=[(None,None)]*cx.nc,method='highs')
            assert mn.success and mx.success
            assert abs(mn.fun-rlo[v])<1e-6 and abs(-mx.fun-rhi[v])<1e-6
