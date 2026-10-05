"""The full, local Stage 1 landscape gate (density matrices are expensive)."""
import numpy as np
import pytest
from certmorse.instances import load_instance
from certmorse.landscape import exact_landscape, exact_points

IDS=['R6a','R6b','R8a','R8b','R8c','R10a','E8a','E8b','W8a','W8b','C8','K5']


@pytest.mark.parametrize('name',IDS)
@pytest.mark.parametrize('channel',['a','b','c'])
def test_T19_continuous_all_instances(name,channel):
    points=np.random.default_rng(19).uniform([0,0],[2*np.pi,np.pi],(100,2))
    f,_,_=exact_points(load_instance(name),list(points)+list(-points),channel,7)
    assert np.max(np.abs(f[:100]-f[100:]))<1e-12


@pytest.mark.parametrize('name',IDS)
@pytest.mark.parametrize('channel',['d','d0','e'])
def test_T25_direct_periodicity(name,channel):
    rng=np.random.default_rng(25)
    points=list(zip(rng.uniform(0,2*np.pi,5),rng.uniform(0,np.pi,5)))
    translated=[(g+2*np.pi,b) for g,b in points]
    f,_,_=exact_points(load_instance(name),points+translated,channel,7)
    assert np.max(np.abs(f[:5]-f[5:]))<1e-12
