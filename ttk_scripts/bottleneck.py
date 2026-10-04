from common import arguments, source, pv, configure

args=arguments()
if not args.in_other: raise ValueError('--in-other must name the second vertex-field VTU')
# Reference adapter; project-reported diagram distances use GUDHI (§6.8).
diagrams=[pv.TTKPersistenceDiagram(Input=source(path),ScalarField=['POINTS','Scalar']) for path in [args.input,args.in_other]]
filt=pv.TTKBottleneckDistance(Input=pv.GroupDatasets(Input=diagrams,OutputType='vtkMultiBlockDataSet'))
configure(filt)
pv.SaveData(args.out,proxy=filt,Precision=17)
