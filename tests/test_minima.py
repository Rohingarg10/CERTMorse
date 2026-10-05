"""T36: resolution proposition, elder merges, and independent GUDHI pairs."""
import json
from pathlib import Path
import numpy as np
import gudhi

from certmorse.complex import TorusComplex
from certmorse.instances import load_instance
from certmorse.legacy_scores import ROOT, saved_path
from certmorse.metrics import BASIN_TOLERANCE
from certmorse.minima import (neighbours, persistence_pairs, minimum_regions, certified_traps,
                             true_basins, resolved_probability)


def test_T36a_resolution_proposition_on_400_random_smooth_fields():
    rng = np.random.default_rng(36)
    for trial in range(400):
        m = int(rng.integers(6, 13)); cx = TorusComplex(m)
        x, y = np.meshgrid(2*np.pi*np.arange(m)/m, 2*np.pi*np.arange(m)/m)
        field = sum(rng.normal()*np.cos(a*x+b*y+rng.uniform(0, 2*np.pi))
                    for a, b in [(1, 0), (0, 1), (1, 1), (2, 0), (0, 2), (2, 1), (1, 2)])
        field += rng.normal(scale=1e-9, size=field.shape)
        W = float(field.max()-field.min()+1); tau = BASIN_TOLERANCE*W
        amplitude = 10**rng.uniform(-3, .3)
        lower = field-rng.uniform(.01, 1, size=field.shape)*amplitude
        upper = field+rng.uniform(.01, 1, size=field.shape)*amplitude
        width = float(np.max(upper-lower)); resolution = 2*width
        pairs = persistence_pairs(field, cx)
        visible = [p for p in pairs if p.persistence > resolution]
        regions = minimum_regions(lower, upper, cx)
        traps = certified_traps(lower, upper, W, cx, regions=regions)
        case = dict(trial=trial, m=m, w_max=width, resolution=resolution,
                    k_min=len(regions), n_visible=len(visible), traps=len(traps), tau=tau)
        assert len(regions) >= len(visible), case
        flat = field.ravel()
        strict = {v for v in range(cx.nv) if all(flat[v] < flat[w] for w in neighbours(m)[v])}
        for trap in traps:
            assert any(v in strict and flat[v] > flat.min()+tau for v in trap), dict(case, trap=list(trap))
        deep = [p for p in visible if p.birth > flat.min()+resolution+tau]
        assert len(traps) >= len(deep), dict(case, n_deep_visible=len(deep))


def saved_fields():
    report = json.loads((ROOT/'docs/resolution-v1.8.3.json').read_text(encoding='utf-8'))
    assert len(report['rows']) == 20
    for row in report['rows']:
        with np.load(saved_path(row['run_path'])/'field.npz') as data:
            yield row, data['truth'].copy()


def test_T36b_resolved_probability_endpoints_on_all_20_saved_fields():
    for row, field in saved_fields():
        cx = TorusComplex(row['grid_m']); W = load_instance(row['instance']).W
        pairs, labels = persistence_pairs(field, cx), true_basins(field, cx)
        zero = resolved_probability(field, W, cx, 0, pairs=pairs, labels=labels)
        infinity = resolved_probability(field, W, cx, np.inf, pairs=pairs, labels=labels)
        assert zero == row['P0_grid'], (row['instance'], cx.m, zero, row['P0_grid'])
        assert infinity == 1, (row['instance'], cx.m, infinity)


def test_T36c_pairs_equal_gudhi_on_all_20_saved_fields():
    for row, field in saved_fields():
        cx = TorusComplex(row['grid_m']); flat = field.ravel()
        tree = gudhi.SimplexTree()
        for vertex, value in enumerate(flat):
            tree.insert([vertex], filtration=float(value))
        for a, b in cx.edge_vertices:
            tree.insert([int(a), int(b)], filtration=float(max(flat[a], flat[b])))
        tree.compute_persistence(homology_coeff_field=2, min_persistence=0)
        independent = tree.persistence_intervals_in_dimension(0)
        ours = np.array([[p.birth, p.death] for p in persistence_pairs(field, cx)])
        sort = lambda a: a[np.lexsort((a[:, 1], a[:, 0]))]
        np.testing.assert_array_equal(sort(ours), sort(independent), err_msg=f"{row['instance']} m={cx.m}")


def test_T36d_E8a_two_non_global_minima_are_sub_resolution():
    row, field = next((row, field) for row, field in saved_fields() if row['instance'] == 'E8a' and row['grid_m'] == 16)
    cx = TorusComplex(16); W = load_instance('E8a').W
    pairs = persistence_pairs(field, cx)
    traps = [p for p in pairs if p.birth > field.min()+BASIN_TOLERANCE*W]
    assert len(traps) == 2
    assert all(0 < p.persistence < .02 for p in traps), [(p.birth, p.persistence) for p in traps]
