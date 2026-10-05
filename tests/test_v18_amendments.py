"""Normative v1.8/v1.8.1 checks; the original T29 failure stays in its XML log."""
import json
from pathlib import Path
import numpy as np
import pytest
from certmorse.instances import load_instance
from certmorse.landscape import (exact_points, exact_landscape, BETA_PERIODS,
                                measured_symmetry, field_diagnostics, run)
from certmorse.grid import GRID_OFFSET, grid_point
from certmorse.complex import TorusComplex, lower_star_gradient
from certmorse.runid import default_config

INSTANCE_IDS = ['R6a', 'R6b', 'R8a', 'R8b', 'R8c', 'R10a',
                'E8a', 'E8b', 'W8a', 'W8b', 'C8', 'K5']
SYMMETRY_TOLERANCE = 1e-12  # v1.8.1 T29
SYMMETRY_POINTS = 100  # v1.8.1 T29
FULL_BETA_PERIOD = np.pi  # v1.8.1 section 2
HALF_BETA_PERIOD = np.pi/2  # v1.8.1 section 2
DAMPING_CONTROL_TOLERANCE = 1e-6  # v1.8.1 T29.3
TEST_SEED = 29  # Reproducible T29 points; original failing run used seed 29.
PIPELINE_SEED = 7  # Retain the original failing run's transpilation.
RECORD_ROOT = None


@pytest.fixture(autouse=True)
def isolated_records(tmp_path):
    global RECORD_ROOT
    RECORD_ROOT = tmp_path


def record(name, values):
    path = RECORD_ROOT/name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(values, indent=2)+'\n', encoding='utf-8', newline='\n')


@pytest.mark.parametrize('name', INSTANCE_IDS)
@pytest.mark.parametrize('channel', ['a', 'b', 'c', 'd', 'd0', 'e'])
def test_T29_beta_period_all_channels(name, channel):
    rng = np.random.default_rng(TEST_SEED)
    points = rng.uniform([0, 0], [2*np.pi, HALF_BETA_PERIOD], (SYMMETRY_POINTS, 2))
    field, _, _ = exact_points(load_instance(name),
                              list(points)+list(points+[0, FULL_BETA_PERIOD])+
                              list(points+[0, HALF_BETA_PERIOD]), channel, PIPELINE_SEED)
    base, full, half = np.split(field, 3)
    full_error = float(np.max(np.abs(base-full)))
    half_error = float(np.max(np.abs(base-half)))
    record(f'T29/{name}-{channel}.json', dict(instance=name, channel=channel,
           full_period_error=full_error, half_period_error=half_error,
           points=SYMMETRY_POINTS, point_seed=TEST_SEED, pipeline_seed=PIPELINE_SEED))
    assert full_error < SYMMETRY_TOLERANCE, (name, channel, full_error)
    if channel != 'c':
        assert half_error < SYMMETRY_TOLERANCE, (name, channel, half_error)
    elif name == 'R8a':
        assert half_error > DAMPING_CONTROL_TOLERANCE, 'amplitude damping must break the half period'


@pytest.mark.parametrize('name', INSTANCE_IDS)
def test_T29_ideal_gamma_metadata(name):
    inst = load_instance(name)
    measured = measured_symmetry(inst, 'a', PIPELINE_SEED)
    record(f'T29/{name}-gamma.json', measured)
    assert measured['gamma_symmetry'] == inst.gamma_symmetry
    assert measured['copies'] == inst.copies
    assert measured['beta_period'] == HALF_BETA_PERIOD


@pytest.mark.parametrize('channel', ['a', 'c'])
def test_per_channel_landscape_metadata(channel, tmp_path):
    cfg = default_config(dict(experiment='stage1-metadata-v1.8.1', instance='R8a',
                              grid_m=3, noise=channel, seed=PIPELINE_SEED))
    run(cfg, tmp_path)
    with np.load(tmp_path/'landscape.npz') as data:
        meta = json.loads(str(data['meta']))
        measured = measured_symmetry(load_instance('R8a'), channel, PIPELINE_SEED)
        for key in ('beta_period', 'gamma_symmetry', 'copies', 'symmetry_points'):
            assert meta[key] == measured[key]
        assert GRID_OFFSET == 0.25
        points = [grid_point(i,j,3,BETA_PERIODS[channel]) for j in range(3) for i in range(3)]
        expected, _, _ = exact_points(load_instance('R8a'),
                                      points, channel, PIPELINE_SEED)
        np.testing.assert_allclose(data['exact'].ravel(), expected, atol=SYMMETRY_TOLERANCE, rtol=0)


@pytest.mark.parametrize('name', INSTANCE_IDS)
@pytest.mark.parametrize('m', [16, 32, 48])
def test_T30_quarter_grid_ideal(name, m):
    cx = TorusComplex(m)
    field, _, _ = exact_landscape(load_instance(name), m, 'a', PIPELINE_SEED)
    diagnostics = field_diagnostics(field, cx)
    a, b = lower_star_gradient(field, cx)
    count = cx.nc-2*int(a.sum()+b.sum())
    record(f'T30/{name}-a-{m}.json', dict(**diagnostics, kappa_true=count))
    assert diagnostics['ties_exact'] == 0, (name, m, diagnostics)
    assert count == 2*(diagnostics['strict_minima']+diagnostics['strict_maxima'])


@pytest.mark.parametrize('name', INSTANCE_IDS)
@pytest.mark.parametrize('channel', ['a', 'c'])
def test_T30_common_full_beta_grid(name, channel):
    cx = TorusComplex(16)
    field, _, _ = exact_landscape(load_instance(name), 16, channel, PIPELINE_SEED, common_domain=True)
    diagnostics = field_diagnostics(field, cx)
    record(f'T30/{name}-{channel}-16-common.json', diagnostics)
    assert diagnostics['ties_exact'] == 0, (name, channel, diagnostics)
