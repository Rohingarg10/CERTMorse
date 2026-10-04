from common import arguments, source, persistence_filter, configure, diagram_rows, write_rows

args=arguments()
data=configure(persistence_filter(source(args.input)))
write_rows(args.out, ['birth','death','dim','is_essential'], diagram_rows(data))
