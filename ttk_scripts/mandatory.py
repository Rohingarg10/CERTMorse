from common import arguments, source, pv, configure, write_rows

args=arguments()
filt=pv.TTKMandatoryCriticalPoints(Input=source(args.input), LowerBoundField=['POINTS','Lower'], UpperBoundField=['POINTS','Upper'])
rows=[]
names=['MinimumComponents','JoinSaddleComponents','SplitSaddleComponents','MaximumComponents']
for port,name in enumerate(names):
    from paraview import servermanager
    if port == 0: configure(filt)
    data=servermanager.Fetch(filt,idx=port)
    array=data.GetPointData().GetArray(name)
    if array is None:
        raise RuntimeError(f'missing discovered mandatory array {name}')
    for v in range(data.GetNumberOfPoints()):
        rows.append(dict(kind=name,vertex=v,component=int(array.GetTuple1(v))))
write_rows(args.out,['kind','vertex','component'],rows)
