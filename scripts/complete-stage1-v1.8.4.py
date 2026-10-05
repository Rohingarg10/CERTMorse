"""Only the missing oracle units and seven timeout probes, with resume by default."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np

from certmorse.complex import TorusComplex
from certmorse.forman import witness, NegativeCycle, is_discrete_morse
from certmorse.instances import load_instance, cost_values
from certmorse.landscape import exact_landscape, make_band, sample_landscape
from certmorse.legacy_scores import stage1_folders, verify_T38
from certmorse.raw import solve_band, sample_band, rehydrate, write_json
from certmorse.rng import streams
from certmorse.scoring import score_folder
from certmorse.stage1_scoring import oracle_row
from certmorse.units import ROOT, Unit, file_hash

RAW_ROOT = ROOT/'results/stage1-completion-v1.8.4'
PROBE_ROOT = ROOT/'results/stage1-timeout-probe-v1.8.4'
spec = importlib.util.spec_from_file_location('rescore', ROOT/'scripts/rescore-stage1.py')
rescore = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rescore)


def emit(event, **payload):
    print(json.dumps(dict(event=event, **payload)), flush=True)


def missing_band(instance, seed, reference):
    """The saved shots are reused; exact variances are computed once per field."""
    inst = load_instance(instance)
    field = Unit('landscape', dict(operation='raw_oracle_field', instance=instance,
                 grid_m=16, noise='a', field_seed=1003), root=RAW_ROOT)
    def field_run(work):
        truth, variance, probs = exact_landscape(inst, 16, 'a', 1003)
        np.savez_compressed(work/'field.npz', truth=truth, var_exact=variance, probs=probs)
    field_path = field.run(field_run)/'field.npz'
    band = Unit('landscape', dict(operation='oracle_band_from_saved_shots', instance=instance,
                grid_m=16, noise='a', seed=seed, field_seed=1003, shots=1000, alpha=.05, band_mode='oracle'),
                {'field': field_path, 'saved_shots': reference/'matching.npz'}, root=RAW_ROOT)
    def band_run(work):
        with np.load(reference/'matching.npz') as old, np.load(field_path) as field_data:
            assert np.array_equal(field_data['truth'], old['truth']), (instance, 'truth changed')
            mean, sample_var = sample_landscape((field_data['probs'], cost_values(inst)), 1000, streams(seed)['land'])
            assert np.array_equal(mean, old['mean']), (instance, seed, 'saved shots changed')
            lower, upper = make_band(old['mean'], field_data['var_exact'], sample_var, 1000, inst.W, .05, 'oracle')
            np.savez_compressed(work/'band.npz', truth=old['truth'], mean=old['mean'], lower=lower, upper=upper)
    return band.run(band_run)/'band.npz'


def oracle_completion():
    verify_T38()
    legacy = {(row['instance'], row['band_mode'], row['seed']): (folder, row) for folder, row in stage1_folders()}
    primaries = {}
    for instance in ('E8a', 'W8a'):
        for seed in range(20):
            reference, _ = legacy[instance, 'hoeffding', seed]
            band = missing_band(instance, seed, reference)
            emit('count_start', instance=instance, seed=seed)
            folder = solve_band(band, dict(instance=instance, grid_m=16, noise='a', seed=seed, field_seed=1003,
                                shots=1000, alpha=.05, band_mode='oracle', time_limit_s=600, threads=8), root=RAW_ROOT)
            primaries[instance, seed] = folder
            result = rehydrate(folder)
            emit('count_complete', instance=instance, seed=seed, status=result.status, kappa=result.kappa_opt, wall_s=result.wall_s)
    datasets, table_inputs, records = {}, {}, {}
    for instance in ('R8a', 'E8a', 'W8a'):
        selected, rows, inputs, details = [], [], {}, []
        for seed in range(20):
            if instance == 'R8a':
                folder, base = legacy[instance, 'oracle', seed]
                optimal = base['status'] == 'OPTIMAL'
            else:
                folder = primaries[instance, seed]
                _, base = legacy[instance, 'hoeffding', seed]
                optimal = rehydrate(folder).status == 'OPTIMAL'
            sampling = None
            if optimal and len(selected) < 10:
                selected.append(seed)
                emit('sampling_start', instance=instance, seed=seed)
                sampling = sample_band(folder, dict(instance=instance, grid_m=16, seed=seed, max_optima=20, time_cap_s=300),
                                       root=RAW_ROOT, legacy=instance == 'R8a')
                sample_record = json.loads((sampling/'sampling.json').read_text(encoding='utf-8'))
                emit('sampling_complete', instance=instance, seed=seed, **sample_record)
            if instance == 'R8a':
                row, scored = score_folder(folder, base, sampling_folder=sampling)
                row['raw_path'] = folder.as_posix()
                if sampling is not None:
                    row['sampling_path'] = sampling.as_posix()
            else:
                row, scored = oracle_row(folder, base, sampling_folder=sampling)
            rows.append(row)
            inputs[str(seed)] = scored/'measurement-v1.8.4.json'
            details.append(dict(seed=seed, raw=folder.as_posix(), scoring=scored.as_posix(),
                                sampling=None if sampling is None else sampling.as_posix()))
        assert len(selected) == 10, (instance, selected)
        datasets[instance] = rows
        table_inputs[instance] = inputs
        records[instance] = dict(selected_seeds=selected, bands=details)
    tables = {}
    for instance, rows in datasets.items():
        name = f'docs/stage1-{instance.lower()}-oracle-completion-v1.8.4.csv'
        rescore.csv_table(rows, ROOT/name, table_inputs[instance])
        tables[instance] = name
    report = dict(status='PASS', new_count_solves=40, reused_count_solves=20, oracle_bands=60,
                  sampling_bands=30, count_cap_s=600, sampling_cap_s=300, max_optima=20, threads=8,
                  field_seed=1003, shots=1000, alpha=.05, records=records, tables=tables,
                  tables_sha256={instance: file_hash(ROOT/name) for instance, name in tables.items()})
    write_json(ROOT/'docs/oracle-completion-v1.8.4.json', report)
    emit('oracle_completion', new_count_solves=40, sampling_bands=30)


def timeout_probes():
    verify_T38()
    assert (ROOT/'docs/oracle-completion-v1.8.4.json').is_file(), 'section 6.2 must finish first'
    original = [(folder, row) for folder, row in stage1_folders()
                if row['band_mode'] == 'hoeffding' and row['status'] == 'FEASIBLE']
    assert len(original) == 7
    rows = []
    for folder, row in original:
        emit('probe_start', instance=row['instance'], seed=row['seed'], LB_region=row['LB_region'])
        target = solve_band(folder/'matching.npz', dict(instance=row['instance'], grid_m=16, seed=row['seed'],
                            time_limit_s=1800, threads=8, region_probe=True, warm_start=False),
                            root=PROBE_ROOT, incumbent=folder/'matching.npz')
        result = rehydrate(target)
        state = 'UNKNOWN'
        kappa, lower = None, row['kappa_cert']
        if result.y is not None and result.y.size:
            cx = TorusComplex(16)
            with np.load(target/'matching.npz') as data:
                a, b = cx.split_matching(data['y'])
                assert is_discrete_morse(data['x'], a, b, cx)[0]
                assert not isinstance(witness(a, b, data['cell_lo'], data['cell_hi'], cx), NegativeCycle)
                assert cx.nc-2*int(data['y'].sum()) == row['LB_region']
            state, kappa, lower = 'OPTIMAL_BY_REGION', row['LB_region'], row['LB_region']
        elif result.status == 'INFEASIBLE':
            state, lower = 'INFEASIBLE', row['LB_region']+2
        scored, _ = score_folder(folder, row)
        record = dict(instance=row['instance'], seed=row['seed'], original=folder.as_posix(), probe=target.as_posix(),
                      status_original=row['status'], status_probe=result.status, status_v184=state,
                      LB_region=row['LB_region'], kappa_opt_v184=kappa, kappa_lb_v184=lower,
                      kappa_incumbent_original=row['kappa_incumbent'], P_incumbent_original=scored['P_incumbent'],
                      wall_s=result.wall_s, time_cap_s=1800, threads=8)
        rows.append(record)
        emit('probe_complete', **record)
    inputs = {str(i): Path(row['probe'])/'solve.json' for i, row in enumerate(rows)}
    # Include the non-optimal comparison and recorded timings in table inputs.
    for i, row in enumerate(rows):
        inputs[f'timing-{i}'] = Path(row['probe'])/'timing.json'
        inputs[f'original-{i}'] = Path(row['original'])/'measurement.json'
    rescore.csv_table(rows, ROOT/'docs/timeout-probe-v1.8.4.csv', inputs)
    write_json(ROOT/'docs/timeout-probe-v1.8.4.json', dict(status='PASS', bands=7, rows=rows))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=['oracle', 'probes', 'all'], default='all')
    args = parser.parse_args()
    if args.phase in ('oracle', 'all'):
        oracle_completion()
    if args.phase in ('probes', 'all'):
        timeout_probes()
