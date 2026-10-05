"""Run under pvpython. Record actual filter properties and VTK arrays."""
import argparse,json,os
import paraview
import paraview.simple as pv
from paraview import servermanager

parser=argparse.ArgumentParser();parser.add_argument('--in',dest='input',required=True);parser.add_argument('--out',required=True)
args=parser.parse_args()
plugin=os.environ.get('CERTMORSE_TTK_PLUGIN')
if plugin: pv.LoadPlugin(plugin,remote=False)
source=pv.XMLUnstructuredGridReader(FileName=[args.input]);source.UpdatePipeline()
report={'paraview':paraview.__version__,'filters':{}}
names=['TTKPersistenceDiagram','TTKScalarFieldCriticalPoints','TTKDiscreteGradient','TTKMorseSmaleComplex','TTKTopologicalSimplification','TTKMandatoryCriticalPoints','TTKBottleneckDistance','TTKPeriodicGrid']
for name in names:
    entry={}
    try:
        factory=getattr(pv,name)
        entry['available']=True
        filt=factory()
        properties=filt.ListProperties();entry['properties']=properties
        if 'Input' in properties:
            if name == 'TTKBottleneckDistance':
                diagram=pv.TTKPersistenceDiagram(Input=source,ScalarField=['POINTS','Scalar'])
                filt.Input=pv.GroupDatasets(Input=[diagram,diagram])
            else: filt.Input=source
        if 'InputDomain' in properties: filt.InputDomain=source
        if 'Domain' in properties: filt.Domain=source
        if 'InputConstraints' in properties:
            critical=pv.TTKScalarFieldCriticalPoints(Input=source,ScalarField=['POINTS','Scalar'])
            filt.InputConstraints=critical
        if 'Constraints' in properties:
            filt.Constraints=pv.TTKPersistenceDiagram(Input=source,ScalarField=['POINTS','Scalar'])
        for prop in ('ScalarField','InputScalars','ScalarFieldName'):
            if prop in properties: setattr(filt,prop,['POINTS','Scalar'])
        for prop,field in [('LowerBoundField','Lower'),('UpperBoundField','Upper')]:
            if prop in properties: setattr(filt,prop,['POINTS',field])
        filt.UpdatePipeline()
        data=servermanager.Fetch(filt)
        entry['point_arrays']=[data.GetPointData().GetArrayName(i) for i in range(data.GetPointData().GetNumberOfArrays())] if hasattr(data,'GetPointData') else []
        entry['cell_arrays']=[data.GetCellData().GetArrayName(i) for i in range(data.GetCellData().GetNumberOfArrays())] if hasattr(data,'GetCellData') else []
        if name == 'TTKPersistenceDiagram':
            entry['pairs']=[dict(Birth=float(data.GetCellData().GetArray('Birth').GetTuple1(i)),Persistence=float(data.GetCellData().GetArray('Persistence').GetTuple1(i)),PairType=int(data.GetCellData().GetArray('PairType').GetTuple1(i)),IsFinite=int(data.GetCellData().GetArray('IsFinite').GetTuple1(i)),endpoints=[float(data.GetPoint(j)[0]) for j in (data.GetCell(i).GetPointId(0),data.GetCell(i).GetPointId(1))]) for i in range(data.GetNumberOfCells())]
        if name == 'TTKMandatoryCriticalPoints':
            entry['ports']={}
            for port in range(4):
                output=servermanager.Fetch(filt,idx=port)
                entry['ports'][str(port)]=[output.GetPointData().GetArrayName(i) for i in range(output.GetPointData().GetNumberOfArrays())]
        if name == 'TTKTopologicalSimplification':
            entry['output_points']=data.GetNumberOfPoints()
        entry['available']=True
        try:
            csv=args.out.replace('.json',f'-{name}.csv')
            pv.SaveData(csv,proxy=filt,FieldAssociation='Cell Data' if entry['cell_arrays'] else 'Point Data',Precision=17)
            with open(csv,encoding='utf8') as stream: entry['csv_header']=stream.readline().strip()
        except Exception as exc: entry['csv_error']=str(exc)
    except AttributeError as exc:
        entry.setdefault('available',False)
        entry['error']=str(exc)
    except Exception as exc: entry['error']=str(exc)
    report['filters'][name]=entry
with open(args.out,'w',encoding='utf-8', newline='\n') as stream: json.dump(report,stream,indent=2)
print(json.dumps(report,indent=2))
