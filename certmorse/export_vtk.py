import numpy as np
import vtk
from vtk.util.numpy_support import numpy_to_vtk
from .grid import GRID_OFFSET, GAMMA_PERIOD, grid_point


def export_complex(cx,path,fields,*,beta_period=np.pi,qaoa=False):
    grid=vtk.vtkUnstructuredGrid()
    points=vtk.vtkPoints()
    points.SetDataTypeToDouble()
    for v in range(cx.nv):
        # Synthetic fields retain the exact unshifted v1.6 parameterisation.
        offset=0 if qaoa else GRID_OFFSET
        gamma,beta=grid_point(v%cx.m-offset,v//cx.m-offset,cx.m,beta_period)
        angle=GAMMA_PERIOD*beta/beta_period  # Embed the beta circle in R^3.
        points.InsertNextPoint((2+np.cos(angle))*np.cos(gamma),(2+np.cos(angle))*np.sin(gamma),np.sin(angle))
    grid.SetPoints(points)
    for triangle in cx.tri_vertices:
        ids=vtk.vtkIdList()
        for v in triangle: ids.InsertNextId(int(v))
        grid.InsertNextCell(vtk.VTK_TRIANGLE,ids)
    for name,values in fields.items():
        values=np.asarray(values).reshape(-1)
        if len(values)!=cx.nv: raise ValueError('one scalar value per vertex required')
        array=numpy_to_vtk(np.ascontiguousarray(values),deep=True)
        array.SetName(name)
        grid.GetPointData().AddArray(array)
    writer=vtk.vtkXMLUnstructuredGridWriter()
    writer.SetFileName(str(path));writer.SetInputData(grid)
    if not writer.Write(): raise IOError(f'could not write {path}')
