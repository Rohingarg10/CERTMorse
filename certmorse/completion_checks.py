"""Read-only verification of completion and probe evidence; see docs/METHOD.md."""
import csv
from hashlib import sha256
import json
from pathlib import Path
import re
import numpy as np

from .complex import TorusComplex
from .forman import is_discrete_morse, witness, NegativeCycle
from .legacy_scores import stage1_folders, verify_T38
from .metrics import critical_counts
from .mip.regions import region_bound
from .scoring import score_arrays
from .units import ROOT, complete_unit, file_hash, UNIT_TYPES


def check_unit(folder):
    folder = Path(folder)
    assert complete_unit(folder), str(folder)
    config = json.loads((folder/'config.json').read_text(encoding='utf-8'))
    identity = dict(config)
    identifier = identity.pop('unit_id')
    assert sha256(json.dumps(identity, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest() == identifier
    assert folder.name == identifier
    assert config['deterministic'] is UNIT_TYPES[config['unit_type']]['deterministic']
    for name, digest in config['source_sha256'].items():
        assert file_hash(ROOT/name) == digest, (folder, name, 'source differs')
    return config


def check_matching(cx, arrays, y, count, x=None):
    a, b = cx.split_matching(y)
    checked = witness(a, b, arrays['cell_lo'], arrays['cell_hi'], cx)
    assert not isinstance(checked, NegativeCycle)
    assert is_discrete_morse(checked, a, b, cx)[0]
    if x is not None:
        assert is_discrete_morse(x, a, b, cx)[0]
        assert np.all((arrays['cell_lo'] <= x) & (x <= arrays['cell_hi']))
    assert cx.nc-2*int(y.sum()) == count


def completion_checks():
    legacy = {(row['instance'], row['band_mode'], row['seed']): (folder, row) for folder, row in stage1_folders()}
    old_hashes = json.loads((ROOT/'docs/rescoring-v1.8.4.json').read_text(encoding='utf-8'))['input_sha256']
    for name, digest in old_hashes.items():
        assert file_hash(ROOT/name) == digest, (name, 'saved input changed')
    reproduced = verify_T38()
    report = json.loads((ROOT/'docs/oracle-completion-v1.8.4.json').read_text(encoding='utf-8'))
    assert report['status'] == 'PASS' and report['new_count_solves'] == 40 and report['sampling_bands'] == 30
    cx = TorusComplex(16)
    totals = {}
    for instance in ('R8a', 'E8a', 'W8a'):
        dataset = report['records'][instance]
        assert [band['seed'] for band in dataset['bands']] == list(range(20))
        rows, samples, optimal = [], 0, []
        for band in dataset['bands']:
            folder = Path(band['raw'])
            scored = Path(band['scoring'])
            check_unit(scored)
            row = json.loads((scored/'measurement-v1.8.4.json').read_text(encoding='utf-8'))
            with np.load(folder/'matching.npz') as data:
                arrays = {key: data[key] for key in data.files}
            if instance == 'R8a':
                expected, base = legacy[instance, 'oracle', band['seed']]
                assert folder.resolve() == expected.resolve()
            else:
                config = check_unit(folder)
                cfg = config['configuration']
                assert cfg['seed'] == band['seed'] and cfg['time_limit_s'] == 600 and cfg['threads'] == 8
                assert cfg['solver'] == 'cpsat' and cfg['formulation'] == 'A' and not cfg['region_probe']
                assert cfg['field_seed'] == 1003 and cfg['shots'] == 1000 and cfg['alpha'] == .05
                _, base = legacy[instance, 'hoeffding', band['seed']]
                assert row['instance'] == instance and row['band_mode'] == 'oracle'
            check_matching(cx, arrays, arrays['y'], row['kappa_incumbent'], arrays['x'])
            regions = region_bound(arrays['cell_lo'], arrays['cell_hi'], cx)
            assert regions.LB_region == row['LB_region']
            if row['status'] == 'OPTIMAL':
                optimal.append(band['seed'])
                assert row['kappa_opt'] == row['kappa_lb'] == row['kappa_incumbent']
            sampled = None
            if band['sampling'] is not None:
                assert row['status'] == 'OPTIMAL'
                sample_folder = Path(band['sampling'])
                config = check_unit(sample_folder)
                cfg = config['configuration']
                assert cfg['seed'] == band['seed'] and cfg['max_optima'] == 20 and cfg['time_cap_s'] == 300
                assert config['input_sha256']['matching'] == file_hash(folder/'matching.npz')
                with np.load(sample_folder/'samples.npz') as data:
                    sampled = data['optima'].copy()
                assert 1 <= len(sampled) <= 20
                assert np.array_equal(sampled[0], arrays['y'])
                ve = len(cx.pairs_ve)
                assert len({y[:ve].tobytes() for y in sampled}) == len(sampled)
                for y in sampled:
                    check_matching(cx, arrays, y, row['kappa_opt'])
                for log in sample_folder.glob('sampling-*.log'):
                    text = log.read_text(encoding='utf-8')
                    assert 'stop_after_first_solution: true' in text and 'num_workers: 8' in text
                    caps = re.findall(r'max_time_in_seconds: (\S+)', text)
                    assert len(caps) == 1 and 0 < float(caps[0]) <= 300
                samples += len(sampled)
            regenerated = score_arrays(arrays, row, sampled)
            assert regenerated == row, (instance, band['seed'], 'scoring differs')
            rows.append(row)
        assert dataset['selected_seeds'] == optimal[:10]
        assert [band['seed'] for band in dataset['bands'] if band['sampling'] is not None] == optimal[:10]
        assert len(optimal[:10]) == 10
        table = ROOT/report['tables'][instance]
        assert file_hash(table) == report['tables_sha256'][instance]
        with table.open(encoding='utf-8', newline='\n') as stream:
            table_rows = list(csv.DictReader(stream))
        assert len(table_rows) == 20
        for row, table_row in zip(rows, table_rows):
            for key in row:
                assert table_row[key] == ('' if row[key] is None else str(row[key])), (instance, row['seed'], key)
        totals[instance] = dict(oracle_bands=20, optimal=len(optimal), sampled_bands=10, sampled_optima=samples,
                               selected_seeds=dataset['selected_seeds'])
    return dict(status='PASS', instances=totals, T38=reproduced,
                v183_inputs_unchanged=len(old_hashes))


def probe_checks():
    report = json.loads((ROOT/'docs/timeout-probe-v1.8.4.json').read_text(encoding='utf-8'))
    assert report['status'] == 'PASS' and len(report['rows']) == report['bands'] == 7
    original = {(row['instance'], row['seed']): (folder, row) for folder, row in stage1_folders()
                if row['band_mode'] == 'hoeffding' and row['status'] == 'FEASIBLE'}
    assert {(r['instance'], r['seed']) for r in report['rows']} == set(original)
    cx = TorusComplex(16)
    outcomes = {}
    for row in report['rows']:
        folder, base = original[row['instance'], row['seed']]
        target = Path(row['probe'])
        config = check_unit(target)
        cfg = config['configuration']
        assert cfg['seed'] == base['seed'] and cfg['threads'] == 8 and cfg['time_limit_s'] == 1800
        assert cfg['region_probe'] and cfg['solver'] == 'cpsat' and cfg['formulation'] == 'A'
        assert config['input_sha256']['incumbent'] == config['input_sha256']['band'] == file_hash(folder/'matching.npz')
        with np.load(target/'matching.npz') as data:
            arrays = {key: data[key] for key in data.files}
        if row['status_v184'] == 'OPTIMAL_BY_REGION':
            check_matching(cx, arrays, arrays['y'], base['LB_region'], arrays['x'])
            c0, _, c2 = critical_counts(arrays['y'], cx)
            assert c0 == base['region_minima'] and c2 == base['region_maxima']
            assert row['kappa_opt_v184'] == row['kappa_lb_v184'] == base['LB_region']
        elif row['status_v184'] == 'INFEASIBLE':
            assert row['status_probe'] == 'INFEASIBLE' and row['kappa_lb_v184'] == base['LB_region']+2
        else:
            assert row['status_v184'] == 'UNKNOWN' and row['kappa_lb_v184'] == base['kappa_cert']
        outcomes[row['status_v184']] = outcomes.get(row['status_v184'], 0)+1
    return dict(status='PASS', bands=7, outcomes=outcomes)
