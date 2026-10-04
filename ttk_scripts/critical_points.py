from common import arguments, source, pv, configure, write_rows

args=arguments()
data=configure(pv.TTKDiscreteGradient(Input=source(args.input), ScalarField=['POINTS','Scalar']))
arrays=data.GetPointData()
rows=[dict(dim=int(arrays.GetArray('CellDimension').GetTuple1(i)),cell=int(arrays.GetArray('CellId').GetTuple1(i)),value=float(arrays.GetArray('Scalar').GetTuple1(i))) for i in range(data.GetNumberOfPoints())]
write_rows(args.out,['dim','cell','value'],rows)
