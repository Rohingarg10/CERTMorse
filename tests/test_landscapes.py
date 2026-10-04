import numpy as np
import pytest
from scipy.stats import norm
from certmorse.instances import load_instance,cost_values,maxcut_closed_form,independent_landscape
from certmorse.landscape import exact_landscape,circuit,sample_landscape,make_band
from qiskit.quantum_info import Statevector

IDS=['R6a','R6b','R8a','R8b','R8c','R10a','E8a','E8b','W8a','W8b','C8','K5']


@pytest.mark.parametrize('name',IDS)
def test_T2_T2b_closed_forms(name):
    inst=load_instance(name)
    m=16
    F,var,probs=exact_landscape(inst,m,'a',7)
    if all(w==1 for w in inst.weights):
        assert np.max(np.abs(F-maxcut_closed_form(inst,2*np.pi*np.arange(m)/m,np.pi*np.arange(m)/m)))<1e-9
    for j in range(m):
        for i in range(m):
            assert abs(F[j,i]-independent_landscape(inst,2*np.pi*i/m,np.pi*j/m))<1e-9
    assert np.max(np.abs(F-F[np.ix_((-np.arange(m))%m,(-np.arange(m))%m)]))<1e-12


@pytest.mark.parametrize('channel',['a','b','c','d','d0','e'])
def test_T1_T19_T25_channels(channel):
    inst=load_instance('R8a')
    F,var,p=exact_landscape(inst,4,channel,7)
    FF,_,_=exact_landscape(inst,4,channel,7)
    assert np.max(np.abs(F-FF))<=1e-12
    if channel in ('a','b','c'):
        assert np.max(np.abs(F-F[np.ix_((-np.arange(4))%4,(-np.arange(4))%4)]))<1e-12
    assert np.all(var>=0)
    assert p.dtype==np.float32


@pytest.mark.parametrize('name',IDS)
def test_T27_off_grid_translation(name):
    inst=load_instance(name)
    qc,gamma,beta=circuit(inst,'d0')
    rng=np.random.default_rng(27)
    differences=[]
    for _ in range(100):
        g,b=rng.uniform(0,2*np.pi),rng.uniform(0,np.pi)
        p=Statevector.from_instruction(qc.assign_parameters({gamma:g,beta:b})).probabilities()
        differences.append(abs(-p@cost_values(inst)-independent_landscape(inst,g-.05,b)))
    if name.startswith('W'): assert max(differences)>1e-3
    else: assert max(differences)<1e-12


def test_T3_band_formula():
    mean=np.array([[-1.,-2.]])
    variance=np.array([[.5,.7]])
    lo,hi=make_band(mean,variance,variance,1000,5,.05,'oracle')
    h=norm.ppf(1-.05/4)*np.sqrt(variance/1000)
    np.testing.assert_allclose(lo,mean-h)
    np.testing.assert_allclose(hi,mean+h)
    lo2,hi2=make_band(mean,variance,np.zeros_like(variance),20,5,.05,'empirical',21)
    lo3,hi3=make_band(mean,variance,variance,20,5,.05,'hoeffding',21)
    assert np.array_equal(lo2,lo3) and np.array_equal(hi2,hi3)
