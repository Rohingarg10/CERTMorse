from common import arguments, source, pv, configure

args=arguments()
filt=pv.TTKMorseSmaleComplex(Input=source(args.input),ScalarField=['POINTS','Scalar'])
configure(filt)
pv.SaveData(args.out,proxy=pv.OutputPort(filt,3),FieldAssociation='Point Data',Precision=17)
