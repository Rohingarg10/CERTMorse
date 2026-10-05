"""Check provenance of supplemental Stage 1 sampling without new solves."""
import csv
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import yaml
from certmorse.complex import TorusComplex
from certmorse.instances import load_instance
from certmorse.metrics import basin_probability
from certmorse.provenance import source_digest
from certmorse.stage1 import GRID_M, MAX_OPTIMA, SAMPLING_CAP_S, THREADS


def run():
    report = json.loads(Path('docs/multiplicity-completion-v1.8.3.json').read_text(encoding='utf8'))
    assert report['source_digest'] == source_digest()
    driver_digest = sha256(Path('scripts/complete-multiplicity.py').read_bytes()).hexdigest()
    assert report['driver_sha256'] == driver_digest
    checked = {}
    cx = TorusComplex(GRID_M)
    for name in ('R8a', 'E8a', 'W8a'):
        inst = load_instance(name)
        with Path(f'docs/stage1-{name.lower()}-v1.8.3-hoeffding.csv').open(newline='') as stream:
            rows = sorted(csv.DictReader(stream), key=lambda r: int(r['seed']))
        optimal = [r for r in rows if r['status'] == 'OPTIMAL']
        sampled = [r for r in rows if int(r['n_opt_found'])]
        # If fewer than ten optima are available, the gate reports that shortage.
        # Selection must still use exactly the eligible bands in seed order.
        assert [r['seed'] for r in sampled] == [r['seed'] for r in optimal[:10]]
        records = report['instances'][name]
        assert records['sampled_bands'] == len(sampled)
        assert records['optimal_available'] == len(optimal)
        supplements = {r['seed']: r for r in records['supplemental']}
        assert len(supplements) == len(records['supplemental'])
        linked = [r for r in sampled if r.get('multiplicity_run_path')]
        assert {int(r['seed']) for r in linked} == set(supplements)
        for row in sampled:
            primary = Path(f'results/stage1-{name.lower()}-v1.8.3-hoeffding') / row['run_id']
            cfg = yaml.safe_load((primary / 'config.yaml').read_text(encoding='utf8'))
            assert cfg['source_digest'] == source_digest()
            assert cfg['multiplicity']['max_optima'] == MAX_OPTIMA
            assert cfg['multiplicity']['time_cap_s'] == SAMPLING_CAP_S
            log_root = primary
            with np.load(primary / 'matching.npz') as data:
                assert len(data['optima']) == int(row['n_opt_found'])
                assert np.array_equal(data['optima'][0], data['y'])
                scores = [basin_probability(y, data['mean'], inst.W, cx, data['lower'], data['upper'])
                          for y in data['optima']]
                assert np.array_equal(data['sample_P'], [score[0] for score in scores])
                assert np.array_equal(data['sample_P_possible'], [score[1] for score in scores])
                if row.get('multiplicity_run_path'):
                    log_root = Path(row['multiplicity_run_path'])
                    side_cfg = yaml.safe_load((log_root / 'config.yaml').read_text(encoding='utf8'))
                    side_row = json.loads((log_root / 'measurement.json').read_text(encoding='utf8'))
                    assert json.loads((log_root / 'status.json').read_text(encoding='utf8'))['complete']
                    assert side_cfg['source_digest'] == source_digest()
                    assert side_cfg['instance'] == name and side_cfg['seed'] == int(row['seed'])
                    assert side_cfg['grid_m'] == GRID_M and side_cfg['threads'] == THREADS
                    assert side_cfg['multiplicity'] == dict(enabled=True, max_optima=MAX_OPTIMA,
                                                          time_cap_s=SAMPLING_CAP_S)
                    assert Path(side_row['primary_run_path']).resolve() == primary.resolve()
                    assert side_row['driver_sha256'] == driver_digest
                    assert Path(supplements[int(row['seed'])]['run_path']).resolve() == log_root.resolve()
                    for key in ('n_opt_found', 'sampling_status', 'P_lo', 'P_hi', 'P_med'):
                        assert str(side_row[key]) == row[key]
                    with np.load(log_root / 'samples.npz') as side:
                        for key in ('optima', 'sample_P', 'sample_P_possible'):
                            assert np.array_equal(side[key], data[key])
            logs = sorted(log_root.glob('sampling-*.log'))
            assert logs or int(row['n_opt_found']) == MAX_OPTIMA
            for log in logs:
                text = log.read_text(encoding='utf8')
                assert 'stop_after_first_solution: true' in text
                assert f'num_workers: {THREADS}' in text
                caps = re.findall(r'max_time_in_seconds: (\S+)', text)
                assert len(caps) == 1 and 0 < float(caps[0]) <= SAMPLING_CAP_S
        checked[name] = dict(sampled_bands=len(sampled), supplemental_bands=len(linked),
                             selected_seeds=[int(r['seed']) for r in sampled],
                             fixed_caps_verified=True, sidecar_arrays_verified=True,
                             all_saved_basin_scores_recomputed=True)
    return dict(source_digest=source_digest(), supplemental_driver_sha256=driver_digest,
                verifier_sha256=sha256(Path(__file__).read_bytes()).hexdigest(), instances=checked)


if __name__ == '__main__':
    result = run()
    Path('docs/multiplicity-verification-v1.8.3.json').write_text(json.dumps(result, indent=2), encoding='utf-8', newline='\n')
    print(json.dumps(result, indent=2))
