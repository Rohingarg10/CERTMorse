"""Fixed torus indexing from specification D5."""
import numpy as np


class TorusComplex:
    def __init__(self, m: int):
        if not isinstance(m, int) or m < 3:
            raise ValueError("m must be an integer >= 3 (D5)")
        self.m = m
        self.nv = m * m
        self.ne = 3 * self.nv
        self.nt = 2 * self.nv
        self.nc = 6 * self.nv
        vid = lambda i, j: (i % m) + m * (j % m)
        edges, triangles, tri_edges = [], [], []
        for j in range(m):
            for i in range(m):
                v, r, u, d = vid(i, j), vid(i+1, j), vid(i, j+1), vid(i+1, j+1)
                edges.extend(((v, r), (v, u), (v, d)))
                triangles.extend(((v, r, d), (v, d, u)))
                tri_edges.extend(((3*v, 3*v+2, 3*r+1), (3*v+2, 3*v+1, 3*u)))
        self.edge_vertices = np.array(edges, dtype=np.int64)
        self.tri_vertices = np.array(triangles, dtype=np.int64)
        self.tri_edges = np.array(tri_edges, dtype=np.int64)
        self.pairs_ve = np.array([(v, self.nv+e) for e, ends in enumerate(edges) for v in ends], dtype=np.int64)
        self.pairs_et = np.array([(self.nv+e, 4*self.nv+t) for t, es in enumerate(tri_edges) for e in es], dtype=np.int64)
        self.pairs = np.concatenate((self.pairs_ve, self.pairs_et))
        self.vertices = [(v,) for v in range(self.nv)] + edges + triangles
        self.faces = [[] for _ in range(self.nc)]
        for e, ends in enumerate(edges):
            self.faces[self.nv+e] = list(ends)
        for t, es in enumerate(tri_edges):
            self.faces[4*self.nv+t] = [self.nv+e for e in es]
        self.cofaces = [[] for _ in range(self.nc)]
        for c, fs in enumerate(self.faces):
            for f in fs:
                self.cofaces[f].append(c)
        self.dim = np.repeat([0, 1, 2], [self.nv, self.ne, self.nt])

    def split_matching(self, y):
        y = np.asarray(y, dtype=np.int8)
        if y.shape != (len(self.pairs),):
            raise ValueError("invalid matching vector shape")
        return y[:len(self.pairs_ve)].copy(), y[len(self.pairs_ve):].copy()


def lower_star_gradient(g, cx):
    """ProcessLowerStars (Robins--Wood--Sheppard), ordered by (value,index)."""
    g = np.asarray(g).reshape(-1)
    if len(g) != cx.nv or not np.all(np.isfinite(g)):
        raise ValueError("one finite value per vertex required")
    order = np.lexsort((np.arange(cx.nv), g))
    rank = np.empty(cx.nv, dtype=np.int64)
    rank[order] = np.arange(cx.nv)
    owner = np.array([max(vs, key=lambda v: rank[v]) for vs in cx.vertices])
    stars = [[] for _ in range(cx.nv)]
    for c, v in enumerate(owner):
        stars[v].append(c)
    key = lambda c: tuple(sorted((int(rank[v]) for v in cx.vertices[c]), reverse=True))
    partner = {}
    for v in order:
        remaining = set(stars[v]) - {int(v)}
        edges = [c for c in remaining if cx.dim[c] == 1]
        if not edges:
            continue
        e = min(edges, key=key)
        partner[int(v)] = e
        partner[e] = int(v)
        remaining.remove(e)
        while remaining:
            singles = [(c, [f for f in cx.faces[c] if f in remaining]) for c in remaining]
            singles = [(c, fs[0]) for c, fs in singles if len(fs) == 1]
            if singles:
                c, f = min(singles, key=lambda p: key(p[0]))
                partner[c] = f
                partner[f] = c
                remaining.difference_update((c, f))
            else:
                zeros = [c for c in remaining if not any(f in remaining for f in cx.faces[c])]
                if not zeros:
                    raise RuntimeError("lower-star processing stalled")
                remaining.remove(min(zeros, key=key))
    y = np.array([partner.get(int(s)) == int(t) for s, t in cx.pairs], dtype=np.int8)
    return cx.split_matching(y)


def flow(match_ve, cx):
    match = np.asarray(match_ve)
    if match.shape != (len(cx.pairs_ve),) or not np.all((match == 0) | (match == 1)):
        raise ValueError("invalid vertex-edge matching")
    successor = np.full(cx.nv, -1, dtype=np.int64)
    for p in np.flatnonzero(match):
        e, a = divmod(int(p), 2)
        v = cx.edge_vertices[e, a]
        if successor[v] != -1:
            raise ValueError("vertex matched more than once")
        successor[v] = cx.edge_vertices[e, 1-a]
    return successor


def basins(match_ve, cx):
    successor = flow(match_ve, cx)
    labels = np.full(cx.nv, -1, dtype=np.int64)
    for start in range(cx.nv):
        path, seen, v = [], set(), start
        while labels[v] < 0 and successor[v] >= 0:
            if v in seen:
                raise ValueError("cycle in descending flow")
            seen.add(v)
            path.append(v)
            v = int(successor[v])
        root = int(labels[v]) if labels[v] >= 0 else v
        labels[v] = root
        labels[path] = root
    assert np.all(successor[np.unique(labels)] == -1)
    return labels
