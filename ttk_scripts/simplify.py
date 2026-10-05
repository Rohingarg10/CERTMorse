from common import arguments, source, pv, configure, persistence_filter
import numpy as np
from vtk.util.numpy_support import vtk_to_numpy

args=arguments()
domain=source(args.input)
diagram=persistence_filter(domain)
valid=pv.Threshold(Input=diagram,Scalars=['CELLS','PairType'],LowerThreshold=0,UpperThreshold=2)
finite=pv.Threshold(Input=valid,Scalars=['CELLS','Persistence'],LowerThreshold=args.threshold,UpperThreshold=float('inf'))
essential=pv.Threshold(Input=valid,Scalars=['CELLS','IsFinite'],LowerThreshold=0,UpperThreshold=0)
selected=pv.AppendDatasets(Input=[finite,essential])
filt=pv.TTKTopologicalSimplification(Domain=domain,Constraints=selected,ScalarField=['POINTS','Scalar'],VertexIdentifierField=['POINTS','ttkVertexScalarField'])
data=configure(filt)
array=data.GetPointData().GetArray('Scalar')
if array is None or data.GetNumberOfPoints()==0: raise RuntimeError('simplification produced no scalar field')
order=data.GetPointData().GetArray('Scalar_Order')
if order is None: raise RuntimeError('simplification lost the Scalar_Order tie ordering')
with open(args.out, 'w', encoding='utf-8', newline='\n') as stream:
    np.savetxt(stream,np.column_stack((vtk_to_numpy(array),vtk_to_numpy(order))),delimiter=',',header='Scalar,Scalar_Order',comments='')
