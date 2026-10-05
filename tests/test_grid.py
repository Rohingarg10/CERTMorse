"""T35 and the explicit synthetic-grid exception in v1.8.3 section 3."""
from pathlib import Path
import re
import numpy as np
import pytest
import vtk
from qiskit.quantum_info import Statevector
from certmorse.grid import GRID_OFFSET, grid_point, grid_coords
from certmorse.landscape import circuit, exact_landscape, BETA_PERIODS
from certmorse.instances import load_instance, cost_values
from certmorse.complex import TorusComplex
from certmorse.export_vtk import export_complex

GRID_TOLERANCE = 1e-12  # v1.8.3 T35


@pytest.mark.parametrize('m',[3,4,8,16,24,32,48])
@pytest.mark.parametrize('period',[np.pi/2,np.pi])
def test_T35_round_trip(m,period):
    i,j=np.meshgrid(np.arange(m),np.arange(m))
    got=grid_coords(*grid_point(i,j,m,period),m,period)
    np.testing.assert_allclose(got,(i,j),atol=GRID_TOLERANCE,rtol=0)
    assert GRID_OFFSET == 0.25


def test_T35_no_duplicate_parameter_conversions():
    # Synthetic test formulae and the independent archived-review script are
    # intentionally unchanged; this scans all active production modules.
    pattern=re.compile(r'(?:2\s*\*\s*(?:np\.)?pi|GAMMA_PERIOD|beta_period)[^\n;]{0,100}/\s*(?:cx\.)?m\b')
    root=Path(__file__).resolve().parents[1]/'certmorse'
    offenders=[]
    for path in root.rglob('*.py'):
        if path.name=='grid.py': continue
        for number,line in enumerate(path.read_text(encoding='utf8').splitlines(),1):
            if pattern.search(line): offenders.append(f'{path.name}:{number}: {line}')
    assert not offenders, offenders


@pytest.mark.parametrize('name',['R8a','W8a'])
def test_T35_direct_statevector_at_vertices(name):
    inst=load_instance(name);m=16
    field,_,_=exact_landscape(inst,m,'a',7)
    qc,gamma,beta=circuit(inst,'a')
    for j in range(m):
        for i in range(m):
            g,b=grid_point(i,j,m,BETA_PERIODS['a'])
            probabilities=Statevector.from_instruction(qc.assign_parameters({gamma:g,beta:b})).probabilities()
            assert abs(field[j,i]+probabilities@cost_values(inst))<GRID_TOLERANCE


@pytest.mark.parametrize('qaoa',[False,True])
def test_T35_vtk_coordinates_preserve_synthetic_grid(qaoa,tmp_path):
    cx=TorusComplex(4);target=tmp_path/'grid.vtu';period=np.pi
    export_complex(cx,target,{'Scalar':np.zeros(cx.nv)},beta_period=period,qaoa=qaoa)
    reader=vtk.vtkXMLUnstructuredGridReader();reader.SetFileName(str(target));reader.Update()
    for v in range(cx.nv):
        offset=0 if qaoa else GRID_OFFSET
        gamma,beta=grid_point(v%cx.m-offset,v//cx.m-offset,cx.m,period)
        angle=2*beta  # Synthetic beta circle has period pi.
        expected=((2+np.cos(angle))*np.cos(gamma),(2+np.cos(angle))*np.sin(gamma),np.sin(angle))
        np.testing.assert_allclose(reader.GetOutput().GetPoint(v),expected,atol=GRID_TOLERANCE,rtol=0)
