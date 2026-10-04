import numpy as np
import vtk
from vtk.util.numpy_support import numpy_to_vtk


def export_complex(cx,path,fields):
    grid=vtk.vtkUnstructuredGrid()
    points=vtk.vtkPoints()
    points.SetDataTypeToDouble()
    for v in range(cx.nv):
        gamma,beta=2*np.pi*(v%cx.m)/cx.m,2*np.pi*(v//cx.m)/cx.m
        points.InsertNextPoint((2+np.cos(beta))*np.cos(gamma),(2+np.cos(beta))*np.sin(gamma),np.sin(beta))
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
