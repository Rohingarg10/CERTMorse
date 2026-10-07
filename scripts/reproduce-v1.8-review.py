"""Independent reproduction of historical basin, grid and region controls.

Does not call the production basin scorer, the proposed region-bound prototype,
or exact_landscape's grid construction. The evidence includes artifact hashes.
"""
import csv
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import yaml
from certmorse.complex import TorusComplex, lower_star_gradient
from certmorse.instances import load_instance, independent_landscape
from certmorse.landscape import exact_points

TIE_TOLERANCE = 1e-12  # Symmetry and tie comparison tolerance.
BASIN_TOLERANCE = 0.02  # Success depth tolerance as a fraction of total edge weight.
GRID_OFFSET = 0.25  # Quarter-offset QAOA grid; see docs/METHOD.md.
POINTS = 100  # Off-grid symmetry points per instance.


def basin_labels(y, cx):
    successor = np.arange(cx.nv)
    for pair in np.flatnonzero(y[:len(cx.pairs_ve)]):
        edge, slot = divmod(int(pair), 2)
        successor[cx.edge_vertices[edge, slot]] = cx.edge_vertices[edge, 1-slot]
    labels = []
    for v in range(cx.nv):
        seen = set()
        while successor[v] != v:
            assert v not in seen, 'closed descending path'
            seen.add(v)
            v = int(successor[v])
        labels.append(v)
    return np.array(labels)


def minimal_regions(lower, upper, adjacency, ascending):
    components = set()
    for seed in range(len(lower)):
        permitted = lower <= upper[seed] if ascending else upper >= lower[seed]
        component = {seed}
        queue = [seed]
        while queue:
            for neighbor in adjacency[queue.pop()]:
                if permitted[neighbor] and neighbor not in component:
                    component.add(neighbor)
                    queue.append(neighbor)
        components.add(frozenset(component))
    return [r for r in components if not any(other < r for other in components)]


def independent_regions(lo, hi, cx):
    vertices = [set() for _ in range(cx.nv)]
    for a, b in cx.edge_vertices:
        vertices[a].add(int(b))
        vertices[b].add(int(a))
    edge_triangles = [[] for _ in range(cx.ne)]
    for t, edges in enumerate(cx.tri_edges):
        for e in edges:
            edge_triangles[e].append(t)
    triangles = [set() for _ in range(cx.nt)]
    for a, b in edge_triangles:
        triangles[a].add(b)
        triangles[b].add(a)
    minima = minimal_regions(lo[:cx.nv], hi[:cx.nv], vertices, True)
    maxima = minimal_regions(lo[4*cx.nv:], hi[4*cx.nv:], triangles, False)
    return dict(k_min=len(minima), k_max=len(maxima),
                LB_region=2*(len(minima)+len(maxima)))


def tie_count(field, cx):
    values = np.asarray(field).ravel()[cx.edge_vertices]
    return int(np.sum(np.abs(values[:, 0]-values[:, 1]) < TIE_TOLERANCE))


def main():
    report = dict(method='docs/METHOD.md', artifact_hashes={}, basins=[], regions=[],
                  symmetries=[], grids=[])
    cx = TorusComplex(16)
    inst = load_instance('R8a')
    with Path('docs/stage1-r8a-v1.7-oracle.csv').open(newline='', encoding='utf8') as stream:
        rows = list(csv.DictReader(stream))
    artifacts = [Path('results/stage1-r8a-v1.7-oracle')/r['run_id']/'matching.npz' for r in rows]
    assert len(artifacts) == 20
    archived_truth = None
    for path in artifacts:
        report['artifact_hashes'][str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        with np.load(path) as data:
            archived_truth = data['truth'].copy()
            regions = independent_regions(data['cell_lo'], data['cell_hi'], cx)
            report['regions'].append(dict(artifact=str(path), **regions))
            optima = data['optima']
            if not len(optima):
                continue
            truth = data['truth'].ravel()
            ends = truth[cx.edge_vertices]
            is_minimum = np.ones(cx.nv, dtype=bool)
            for (a, b), (fa, fb) in zip(cx.edge_vertices, ends):
                if fa >= fb-TIE_TOLERANCE:
                    is_minimum[a] = False
                if fb >= fa-TIE_TOLERANCE:
                    is_minimum[b] = False
            true_minima = np.flatnonzero(is_minimum & (truth <= truth.min()+BASIN_TOLERANCE*inst.W))
            for index, y in enumerate(optima):
                labels = basin_labels(y, cx)
                roots = np.unique(labels)
                mean = data['mean'].ravel()
                depths = np.array([mean[labels == r].min() for r in roots])
                old_roots = roots[mean[roots] <= mean[roots].min()+BASIN_TOLERANCE*inst.W]
                new_roots = roots[depths <= depths.min()+BASIN_TOLERANCE*inst.W]
                report['basins'].append(dict(artifact=str(path), optimum=index,
                    old_P=float(np.mean(np.isin(labels, old_roots))),
                    depth_P=float(np.mean(np.isin(labels, new_roots))), minima=len(roots),
                    global_minima_per_basin=[int(np.sum(labels[true_minima] == r)) for r in roots]))
    report['old_R8a_ties'] = tie_count(archived_truth, cx)
    instances = yaml.safe_load(Path('configs/instances.yaml').read_text(encoding='utf8'))
    points = np.random.default_rng(1803).uniform([0, 0], [2*np.pi, np.pi/2], (POINTS, 2))
    for name in instances:
        inst = load_instance(name)
        base = np.array([independent_landscape(inst, g, b) for g, b in points])
        beta = np.array([independent_landscape(inst, g, b+np.pi/2) for g, b in points])
        degrees = np.zeros(inst.n, dtype=int)
        for (a, b), w in zip(inst.edges, inst.weights):
            degrees[a] += w
            degrees[b] += w
        symmetry = 'gamma_shift_reflect' if np.all(degrees % 2 == 1) else 'gamma_shift' if np.all(degrees % 2 == 0) else 'none'
        shifted = np.array([independent_landscape(inst, g+np.pi, b) for g, b in points])
        reflected = np.array([independent_landscape(inst, g, -b) for g, b in points])
        gamma_error = float(np.max(np.abs(shifted-(reflected if symmetry == 'gamma_shift_reflect' else base))))
        report['symmetries'].append(dict(instance=name, symmetry=symmetry,
            beta_max_error=float(np.max(np.abs(base-beta))), gamma_max_error=gamma_error))
        for m in (16, 32):
            grid = [(2*np.pi*(i+GRID_OFFSET)/m, (np.pi/2)*(j+GRID_OFFSET)/m)
                    for j in range(m) for i in range(m)]
            field, _, _ = exact_points(inst, grid, 'a', instances[name]['seed'])
            grid_cx = TorusComplex(m)
            report['grids'].append(dict(instance=name, m=m, ties_exact=tie_count(field, grid_cx)))
        print(f'Reproduced {name}', flush=True)
    checks = dict(
        basin_depth=all(r['depth_P'] == 1 and r['minima'] == 8 and all(n == 1 for n in r['global_minima_per_basin']) for r in report['basins']),
        beta_period=all(r['beta_max_error'] < TIE_TOLERANCE for r in report['symmetries']),
        gamma_symmetries=all(r['gamma_max_error'] < TIE_TOLERANCE for r in report['symmetries'] if r['symmetry'] != 'none'),
        old_grid_ties=report['old_R8a_ties'] == 112,
        quarter_grid_ties=all(r['ties_exact'] == 0 for r in report['grids']),
        region_bound=all(r['LB_region'] == 32 and r['k_min'] == r['k_max'] == 8 for r in report['regions']))
    report['checks'] = checks
    report['status'] = 'PASS' if all(checks.values()) else 'FAIL'
    Path('docs/review-reproduction-v1.8.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(status=report['status'], checks=checks,
        sampled_optima=len(report['basins']), old_P_min=min(r['old_P'] for r in report['basins']),
        old_R8a_ties=report['old_R8a_ties']), indent=2), flush=True)
    return 0 if all(checks.values()) else 1


if __name__ == '__main__':
    sys.exit(main())
