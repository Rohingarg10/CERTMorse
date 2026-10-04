"""Closure filtration (§6.8), including essential H2."""
import numpy as np
import gudhi


def closure_filtration(cell_values, cx, scale=1):
    x = np.asarray(cell_values, dtype=np.float64).reshape(-1) / scale
    if len(x) != cx.nc or not np.all(np.isfinite(x)) or scale <= 0:
        raise ValueError("finite cell values and positive scale required")
    phi = x.copy()
    for c in range(cx.nc-1, -1, -1):
        for f in cx.faces[c]:
            phi[f] = min(phi[f], phi[c])
    for c in range(cx.nc):
        assert all(phi[f] <= phi[c] for f in cx.faces[c])
    return phi


def persistence(cell_values, cx, scale):
    phi = closure_filtration(cell_values, cx, scale)
    tree = gudhi.SimplexTree()
    for c in range(cx.nc):
        tree.insert(cx.vertices[c], filtration=float(phi[c]))
    tree.compute_persistence(homology_coeff_field=2, min_persistence=0, persistence_dim_max=True)
    return {q: np.ascontiguousarray(tree.persistence_intervals_in_dimension(q)) for q in (0,1,2)}


def bottleneck(diag_a, diag_b):
    return max(gudhi.bottleneck_distance(diag_a[q], diag_b[q], e=0) for q in (0,1,2))


def lower_star_values(g, cx):
    g = np.asarray(g).reshape(-1)
    return np.array([max(g[list(vs)]) for vs in cx.vertices])
