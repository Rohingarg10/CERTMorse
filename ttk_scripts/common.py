"""TTK 1.3.0 adapter, names established by docs/ttk-discovery.json."""
import argparse
import csv
import os
import paraview
import paraview.simple as pv
from paraview import servermanager


def arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--in', dest='input', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--threshold', type=float, default=0)
    parser.add_argument('--in-other')
    return parser.parse_args()


def source(path):
    if os.environ.get('CERTMORSE_TTK_PLUGIN'):
        pv.LoadPlugin(os.environ['CERTMORSE_TTK_PLUGIN'], remote=False)
    print(f'ParaView {paraview.__version__}; TopologyToolKit plugin {os.environ.get("CERTMORSE_TTK_PLUGIN")}')
    data = pv.XMLUnstructuredGridReader(FileName=[path])
    data.UpdatePipeline()
    return data


def configure(filt):
    filt.UseAllCores = 0
    filt.ThreadNumber = 8
    filt.DebugLevel = 0
    filt.UpdatePipeline()
    return servermanager.Fetch(filt)


def write_rows(path, fields, rows):
    with open(path, 'w', newline='\n', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def persistence_filter(domain):
    return pv.TTKPersistenceDiagram(Input=domain, ScalarField=['POINTS', 'Scalar'], EmbedinDomain=0)


def diagram_rows(data):
    arrays = data.GetCellData()
    required = ['PairType', 'Birth', 'Persistence', 'IsFinite']
    if any(arrays.GetArray(name) is None for name in required):
        raise RuntimeError(f'TTK persistence arrays differ from discovery: {required}')
    rows = []
    for i in range(data.GetNumberOfCells()):
        kind = int(arrays.GetArray('PairType').GetTuple1(i))
        if kind == -1:
            continue  # artificial diagonal display cell, not a persistence pair
        finite = int(arrays.GetArray('IsFinite').GetTuple1(i))
        birth = float(arrays.GetArray('Birth').GetTuple1(i))
        life = float(arrays.GetArray('Persistence').GetTuple1(i))
        if finite:
            if life > 0:
                rows.append(dict(birth=birth, death=birth+life, dim=0 if kind == 0 else 1, is_essential=0))
        else:
            # Discovered TTK 1.3.0 contract: one IsFinite=0 cell per essential
            # class, artificially ending at the global maximum for display.
            rows.append(dict(birth=birth,death=float('inf'),dim=kind,is_essential=1))
    return rows
