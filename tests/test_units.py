"""T37 hard-kill/resume, T39 source isolation, and completion contracts."""
from datetime import datetime, timezone, timedelta
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import numpy as np
import pytest

from certmorse.units import ROOT, UNIT_SOURCES, UNIT_TYPES, Unit, complete_unit, file_hash, fingerprint
from certmorse.complex import TorusComplex
from certmorse.forman import witness, NegativeCycle, is_discrete_morse
from certmorse.instances import load_instance
from certmorse.metrics import basin_probability


def test_T39_scoring_edits_do_not_invalidate_solves(tmp_path):
    files = {'certmorse/units.py'} | {p for family in UNIT_SOURCES.values() for p in family}
    for name in files:
        target = tmp_path/name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT/name, target)
    cfg = dict(instance='R8a', grid_m=16, seed=0, source_digest='old global digest')
    before = {kind: fingerprint(kind, cfg, source_root=tmp_path)[0] for kind in UNIT_SOURCES}
    score = tmp_path/'certmorse/metrics.py'
    score.write_text(score.read_text(encoding='utf-8')+'\n# scoring-only change\n', encoding='utf-8', newline='\n')
    after = {kind: fingerprint(kind, cfg, source_root=tmp_path)[0] for kind in UNIT_SOURCES}
    assert after['scoring'] != before['scoring']
    assert all(after[kind] == before[kind] for kind in before if kind != 'scoring')
    model = tmp_path/'certmorse/mip/model_A.py'
    model.write_text(model.read_text(encoding='utf-8')+'\n# solve change\n', encoding='utf-8', newline='\n')
    assert fingerprint('solve', cfg, source_root=tmp_path)[0] != after['solve']
    cfg['source_digest'] = 'new global digest'
    assert fingerprint('scoring', cfg, source_root=tmp_path)[0] == after['scoring']


def test_unit_hashes_atomic_completion_and_corruption(tmp_path):
    unit = Unit('scoring', dict(seed=1), root=tmp_path, suspensions=[])
    assert unit.prepare()
    (unit.work/'result.json').write_text('{}\n', encoding='utf-8', newline='\n')
    assert not (unit.path/'result.json').exists() and not complete_unit(unit.path)
    unit.finish()
    assert complete_unit(unit.path)
    before = (unit.path/'status.json').read_bytes()
    assert not unit.prepare()
    assert (unit.path/'status.json').read_bytes() == before
    (unit.path/'result.json').write_text('corrupted\n', encoding='utf-8', newline='\n')
    assert not complete_unit(unit.path)
    assert unit.prepare()
    assert len(list((tmp_path/'quarantine').iterdir())) == 1


def test_incomplete_unit_discards_only_tmp(tmp_path):
    unit = Unit('scoring', dict(seed=2), root=tmp_path, suspensions=[])
    assert unit.prepare()
    (unit.work/'partial.json').write_text('partial', encoding='utf-8', newline='\n')
    assert unit.prepare()
    assert not (unit.work/'partial.json').exists()


def test_suspended_unit_is_quarantined(tmp_path):
    unit = Unit('scoring', dict(seed=3), root=tmp_path, suspensions=[])
    assert unit.prepare()
    (unit.work/'result.json').write_text('{}\n', encoding='utf-8', newline='\n')
    unit.finish()
    stamp = datetime.fromisoformat(unit.started_at)
    unit.suspensions = [((stamp-timedelta(seconds=1)).isoformat(), (stamp+timedelta(seconds=1)).isoformat())]
    assert unit.prepare()
    quarantine = next((tmp_path/'quarantine').iterdir())
    assert (quarantine/'result.json').read_bytes() == b'{}\n'
    assert 'suspend' in json.loads((quarantine/'quarantine.json').read_text(encoding='utf-8'))['reason']


def test_coverage_block_limit():
    with pytest.raises(ValueError, match='at most 100'):
        fingerprint('coverage', dict(seed_count=101))


def driver(root, log, env=None):
    stream = log.open('w', encoding='utf-8', newline='\n')
    process = subprocess.Popen([sys.executable, '-B', str(ROOT/'scripts/restartable-stage1.py'),
                                '--root', str(root), '--grid-m', '4', '--bands', '3'],
                               cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, env=env)
    return process, stream


def strip_timing(value):
    if isinstance(value, dict):
        return {k: strip_timing(v) for k, v in value.items() if k not in ('wall_s', 'started_at', 'completed_at')}
    if isinstance(value, list):
        return [strip_timing(v) for v in value]
    return value


def compare_runs(reference, actual):
    evidence = []
    def units(root):
        found = {}
        for config in root.glob('*/*/config.json'):
            record = json.loads(config.read_text(encoding='utf-8'))
            cfg = record['configuration']
            label = record['unit_type']+'/'+str(cfg.get('seed', 'field'))
            assert complete_unit(config.parent), config.parent
            assert record['deterministic'] is UNIT_TYPES[record['unit_type']]['deterministic']
            found[label] = config.parent
        return found
    expected, observed = units(reference), units(actual)
    assert expected.keys() == observed.keys()
    for label in sorted(expected):
        kind = label.split('/')[0]
        if not UNIT_TYPES[kind]['deterministic']:
            continue
        left, right = expected[label], observed[label]
        files = {p.name for p in left.iterdir() if p.is_file()}
        assert files == {p.name for p in right.iterdir() if p.is_file()}
        for name in files:
            if name == 'status.json':
                a, b = [strip_timing(json.loads((p/name).read_text(encoding='utf-8'))) for p in (left, right)]
                assert a == b, (label, name, a, b)
            else:
                assert (left/name).read_bytes() == (right/name).read_bytes(), (label, name)
    for seed in range(3):
        rows = []
        for indexed in (expected, observed):
            solved, sampled = indexed[f'solve/{seed}'], indexed[f'sampling/{seed}']
            record = json.loads((solved/'solve.json').read_text(encoding='utf-8'))
            bounds = json.loads((solved/'bounds.json').read_text(encoding='utf-8'))
            cx = TorusComplex(4)
            with np.load(solved/'matching.npz') as data:
                arrays = {key: data[key] for key in data.files}
            y, x = arrays['y'], arrays['x']
            a, b = cx.split_matching(y)
            assert not isinstance(witness(a, b, arrays['cell_lo'], arrays['cell_hi'], cx), NegativeCycle)
            assert is_discrete_morse(x, a, b, cx)[0]
            assert cx.nc-2*int(y.sum()) == record['kappa_opt']
            with np.load(sampled/'samples.npz') as data:
                optima = data['optima'].copy()
            assert 1 <= len(optima) <= 20
            values = []
            for optimum in optima:
                a, b = cx.split_matching(optimum)
                x = witness(a, b, arrays['cell_lo'], arrays['cell_hi'], cx)
                assert not isinstance(x, NegativeCycle)
                assert is_discrete_morse(x, a, b, cx)[0]
                assert cx.nc-2*int(optimum.sum()) == record['kappa_opt']
                values.append(basin_probability(optimum, arrays['mean'], load_instance('R8a').W, cx, arrays['lower'], arrays['upper'])[0])
            rows.append(dict(status=record['status'], kappa_opt=record['kappa_opt'], kappa_lb=record['kappa_lb'],
                             LB_region=bounds['LB_region'], n_optima=len(optima), P_values=sorted(set(values))))
        a, b = rows
        assert a['status'] == b['status'] == 'OPTIMAL'
        for key in ('kappa_opt', 'kappa_lb', 'LB_region'):
            assert a[key] == b[key], (seed, key, a[key], b[key])
        evidence.append(dict(seed=seed, reference=a, resumed=b, P_sets_differ=a['P_values'] != b['P_values']))
    return evidence


@pytest.mark.parametrize('phase', ['solve', 'file-write'])
def test_T37_hard_kill_and_resume(phase, tmp_path, tmp_path_factory):
    reference, interrupted = tmp_path/'reference', tmp_path/'interrupted'
    process, stream = driver(reference, tmp_path/'reference.log')
    try:
        assert process.wait(timeout=3600) == 0, (tmp_path/'reference.log').read_text(encoding='utf-8')
    finally:
        if process.poll() is None:
            process.kill(); process.wait()
        stream.close()
    marker = tmp_path/'ready.json'
    env = dict(os.environ, CERTMORSE_TEST_PAUSE_PHASE=phase, CERTMORSE_TEST_PAUSE_SEED='1', CERTMORSE_TEST_READY=str(marker))
    process, stream = driver(interrupted, tmp_path/'killed.log', env)
    try:
        deadline = time.monotonic()+3600
        while not marker.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(.05)
        assert marker.exists(), (tmp_path/'killed.log').read_text(encoding='utf-8')
        # subprocess.kill uses TerminateProcess on Windows: no signal handler,
        # no cleanup, no opportunity to write a completion marker.
        process.kill(); process.wait(timeout=60)
    finally:
        if process.poll() is None:
            process.kill(); process.wait()
        stream.close()
    first = next(p for p in (interrupted/'solve').iterdir()
                 if json.loads((p/'.tmp/config.json' if (p/'.tmp/config.json').exists() else p/'config.json').read_text(encoding='utf-8'))['configuration']['seed'] == 0)
    second = next(p for p in (interrupted/'solve').iterdir() if p != first)
    completed = {folder: {p.relative_to(folder).as_posix(): p.read_bytes() for p in folder.rglob('*') if p.is_file()}
                 for folder in interrupted.glob('*/*') if folder.is_dir() and complete_unit(folder)}
    second_start = json.loads((second/'status.json').read_text(encoding='utf-8'))['started_at']
    assert complete_unit(first) and not complete_unit(second)
    assert (second/'.tmp').is_dir()
    # A poisoned partial result demonstrates that restart discards .tmp
    # instead of accepting an interrupted writer's artefact.
    (second/'.tmp/matching.npz').write_bytes(b'poisoned interrupted result')
    process, stream = driver(interrupted, tmp_path/'resumed.log')
    try:
        assert process.wait(timeout=3600) == 0, (tmp_path/'resumed.log').read_text(encoding='utf-8')
    finally:
        if process.poll() is None:
            process.kill(); process.wait()
        stream.close()
    for folder, before in completed.items():
        assert before == {p.relative_to(folder).as_posix(): p.read_bytes() for p in folder.rglob('*') if p.is_file()}
    assert complete_unit(second)
    assert json.loads((second/'status.json').read_text(encoding='utf-8'))['started_at'] != second_start
    evidence = compare_runs(reference, interrupted)
    report = dict(phase=phase, grid_m=4, instance='R8a', band_mode='oracle', seeds=[0, 1, 2], threads=8,
                  solve_cap_s=600, sampling_cap_s=300, max_optima=20, first_band_preserved=True,
                  second_band_restarted=True, partial_file_discarded=True, deterministic_units_byte_identical=True,
                  solver_status_bounds_and_witnesses_verified=True, completed_units_preserved=len(completed),
                  reference=reference.relative_to(ROOT).as_posix(), resumed=interrupted.relative_to(ROOT).as_posix(), seeds_evidence=evidence, status='PASS')
    target = tmp_path_factory.getbasetemp()/f'reports/T37-{phase}-v1.8.4.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8', newline='\n')
