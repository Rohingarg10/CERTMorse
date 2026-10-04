import os
import numpy as np
import pytest
from certmorse.complex import TorusComplex
from certmorse.export_vtk import export_complex
from certmorse.ttk import execute


@pytest.mark.ttk
@pytest.mark.skipif(not os.environ.get('CERTMORSE_PVPYTHON'),reason='configure TTK')
def test_reference_adapters(tmp_path):
    cx=TorusComplex(16)
    v=np.arange(cx.nv)
    g=np.cos(4*np.pi*(v%16)/16)+np.cos(2*np.pi*(v//16)/16)
    source=tmp_path/'field.vtu'
    export_complex(cx,source,{'Scalar':g,'Lower':g-.01,'Upper':g+.01})
    execute('simplify',source,tmp_path/'simplified.csv','--threshold',.1)
    values=np.loadtxt(tmp_path/'simplified.csv',delimiter=',',skiprows=1)
    assert values.shape==(cx.nv,2) and np.all(np.isfinite(values))
    assert len(np.unique(values[:,1]))==cx.nv
    execute('morse_smale',source,tmp_path/'basins.csv')
    assert (tmp_path/'basins.csv').stat().st_size>100
    execute('bottleneck',source,tmp_path/'bottleneck.csv','--in-other',source)
    assert (tmp_path/'bottleneck.csv').stat().st_size>0
