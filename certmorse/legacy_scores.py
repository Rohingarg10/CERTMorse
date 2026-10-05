"""T38: read-only reproduction of every gated v1.8.3 basin score."""
import csv
import json
from pathlib import Path
import numpy as np
import yaml

from .complex import TorusComplex
from .instances import load_instance
from .metrics import basin_probability
from .units import ROOT, file_hash

LEGACY_DIGEST = 'ac3e847b9f8846eb8d599ea96ce128ea49c42ff43bb73da3e2a50d972f41823f'
INSTANCES = ('R8a', 'E8a', 'W8a')


def saved_path(value):
    return ROOT/str(value).replace('\\', '/')


def stage1_folders():
    folders = []
    for name, mode in [('R8a', 'hoeffding'), ('E8a', 'hoeffding'), ('W8a', 'hoeffding'), ('R8a', 'oracle')]:
        directory = ROOT/f'results/stage1-{name.lower()}-v1.8.3-{mode}'
        records = []
        for path in directory.glob('*/measurement.json'):
            row = json.loads(path.read_text(encoding='utf-8'))
            records.append((row['seed'], path.parent, row))
        assert len(records) == 20, (name, mode, len(records))
        folders.extend((folder, row) for _, folder, row in sorted(records))
    return folders


def scores_for_matchings(arrays, matchings, W, cx):
    values = [basin_probability(y, arrays['mean'], W, cx, arrays['lower'], arrays['upper']) for y in matchings]
    return np.array([v[0] for v in values]), np.array([v[1] for v in values])


def verify_T38():
    checks, inputs = [], {}
    primary = stage1_folders()
    for folder, row in primary:
        cfg = yaml.safe_load((folder/'config.yaml').read_text(encoding='utf-8'))
        assert cfg['source_digest'] == LEGACY_DIGEST, folder
        assert json.loads((folder/'status.json').read_text(encoding='utf-8'))['complete'], folder
        with np.load(folder/'matching.npz') as data:
            arrays = {key: data[key] for key in data.files}
        cx = TorusComplex(row['grid_m'])
        W = load_instance(row['instance']).W
        if row['status'] == 'OPTIMAL':
            P, possible = basin_probability(arrays['y'], arrays['mean'], W, cx, arrays['lower'], arrays['upper'])
            assert P == row['P_first'], (folder, 'P_first', P, row['P_first'])
            assert possible == row['P_possible'], (folder, 'P_possible', possible, row['P_possible'])
            if 'P' in row:
                assert P == row['P'], (folder, 'P', P, row['P'])
        sample_P, sample_possible = scores_for_matchings(arrays, arrays['optima'], W, cx)
        assert np.array_equal(sample_P, arrays['sample_P']), (folder, 'sample_P')
        assert np.array_equal(sample_possible, arrays['sample_P_possible']), (folder, 'sample_P_possible')
        assert len(sample_P) == row['n_opt_found'], (folder, len(sample_P), row['n_opt_found'])
        if len(sample_P):
            for key, value in [('P_med', float(np.median(sample_P))), ('P_lo', float(sample_P.min())), ('P_hi', float(sample_P.max()))]:
                assert value == row[key], (folder, key, value, row[key])
        inputs[(folder/'matching.npz').relative_to(ROOT).as_posix()] = file_hash(folder/'matching.npz')
        inputs[(folder/'measurement.json').relative_to(ROOT).as_posix()] = file_hash(folder/'measurement.json')
        checks.append(dict(folder=folder.relative_to(ROOT).as_posix(), instance=row['instance'], band_mode=row['band_mode'],
                           seed=row['seed'], optimal=row['status'] == 'OPTIMAL', sampled_optima=len(sample_P)))
        sidecar = row.get('multiplicity_run_path')
        if sidecar:
            side = saved_path(sidecar)
            record = json.loads((side/'measurement.json').read_text(encoding='utf-8'))
            with np.load(side/'samples.npz') as data:
                values, possible = scores_for_matchings(arrays, data['optima'], W, cx)
                assert np.array_equal(values, data['sample_P']), (side, 'sample_P')
                assert np.array_equal(possible, data['sample_P_possible']), (side, 'sample_P_possible')
                assert np.array_equal(data['optima'], arrays['optima']), (side, 'cached optima')
            for key, value in [('P_med', float(np.median(values))), ('P_lo', float(values.min())), ('P_hi', float(values.max()))]:
                assert value == record[key], (side, key, value, record[key])
            inputs[(side/'samples.npz').relative_to(ROOT).as_posix()] = file_hash(side/'samples.npz')
            inputs[(side/'measurement.json').relative_to(ROOT).as_posix()] = file_hash(side/'measurement.json')
    for name, mode in [('R8a', 'hoeffding'), ('E8a', 'hoeffding'), ('W8a', 'hoeffding'), ('R8a', 'oracle')]:
        path = ROOT/f'docs/stage1-{name.lower()}-v1.8.3-{mode}.csv'
        with path.open(encoding='utf-8', newline='\n') as stream:
            rows = list(csv.DictReader(stream))
        by_id = {row['run_id']: row for _, row in primary if row['instance'] == name and row['band_mode'] == mode}
        assert len(rows) == len(by_id) == 20
        for row in rows:
            record = by_id[row['run_id']]
            for key in ('P', 'P_first', 'P_possible', 'P_med', 'P_lo', 'P_hi'):
                if key in row:
                    value = None if row[key] == '' else float(row[key])
                    assert value == record.get(key), (path, row['seed'], key, value, record.get(key))
        inputs[path.relative_to(ROOT).as_posix()] = file_hash(path)
    return dict(status='PASS', legacy_source_digest=LEGACY_DIGEST, primary_folders=len(primary),
                optimal_bands=sum(row['status'] == 'OPTIMAL' for _, row in primary),
                sampled_optima=sum(row['n_opt_found'] for _, row in primary),
                sidecar_folders=sum(bool(row.get('multiplicity_run_path')) for _, row in primary),
                exact_equality=True, checks=checks, input_sha256=inputs)
