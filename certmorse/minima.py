"""Reported-band traps and elder-rule H0 persistence on the D5 graph."""
from dataclasses import dataclass
from functools import lru_cache
import numpy as np

from .complex import TorusComplex, lower_star_gradient, basins
from .metrics import BASIN_TOLERANCE
from .mip.regions import _regions


@lru_cache(maxsize=None)
def neighbours(m):
    cx = TorusComplex(m)
    graph = [[] for _ in range(cx.nv)]
    for a, b in cx.edge_vertices:
        graph[a].append(int(b)); graph[b].append(int(a))
    return tuple(tuple(sorted(row)) for row in graph)


@dataclass(frozen=True)
class MinimumPair:
    minimum: int
    elder: int | None
    birth: float
    death: float

    @property
    def persistence(self):
        return self.death-self.birth


def persistence_pairs(field, cx):
    values = np.asarray(field, dtype=float).reshape(-1)
    assert values.shape == (cx.nv,) and np.all(np.isfinite(values))
    order = np.lexsort((np.arange(cx.nv), values))
    rank = np.empty(cx.nv, dtype=np.int64); rank[order] = np.arange(cx.nv)
    parent = np.full(cx.nv, -1, dtype=np.int64)
    oldest = np.arange(cx.nv, dtype=np.int64)
    pairs = []
    def find(v):
        while parent[v] != v:
            parent[v] = parent[parent[v]]
            v = int(parent[v])
        return v
    for vertex in order:
        vertex = int(vertex); parent[vertex] = vertex
        for adjacent in neighbours(cx.m)[vertex]:
            if parent[adjacent] < 0:
                continue
            a, b = find(vertex), find(adjacent)
            if a == b:
                continue
            if rank[oldest[a]] > rank[oldest[b]]:
                a, b = b, a
            elder, younger = int(oldest[a]), int(oldest[b])
            if values[vertex] > values[younger]:
                pairs.append(MinimumPair(younger, elder, float(values[younger]), float(values[vertex])))
            parent[b] = a
    essential = int(oldest[find(int(order[0]))])
    pairs.append(MinimumPair(essential, None, float(values[essential]), float('inf')))
    return tuple(sorted(pairs, key=lambda pair: (pair.death, pair.minimum)))


def true_basins(field, cx):
    return basins(lower_star_gradient(field, cx)[0], cx)


def resolved_probability(field, W, cx, threshold, *, pairs=None, labels=None):
    if threshold < 0:
        raise ValueError('nonnegative resolution threshold required')
    values = np.asarray(field, dtype=float).reshape(-1)
    pairs = persistence_pairs(values, cx) if pairs is None else pairs
    labels = true_basins(values, cx) if labels is None else labels
    representatives = {int(root): int(root) for root in np.unique(labels)}
    def find(root):
        while representatives.get(root, root) != root:
            root = representatives[root]
        return root
    for pair in pairs:
        if pair.elder is not None and pair.persistence < threshold:
            representatives[pair.minimum] = find(pair.elder)
    selected = [root for root in np.unique(labels)
                if values[find(int(root))] <= values.min()+BASIN_TOLERANCE*W]
    return float(np.mean(np.isin(labels, selected)))


def minimum_regions(lower, upper, cx):
    lo, hi = np.asarray(lower, dtype=float).reshape(-1), np.asarray(upper, dtype=float).reshape(-1)
    assert lo.shape == hi.shape == (cx.nv,) and np.all(lo <= hi)
    assert np.all(np.isfinite(lo)) and np.all(np.isfinite(hi))
    return _regions(lo, hi, neighbours(cx.m), True)


def certified_traps(lower, upper, W, cx, *, regions=None):
    lo, hi = np.asarray(lower).reshape(-1), np.asarray(upper).reshape(-1)
    regions = minimum_regions(lo, hi, cx) if regions is None else regions
    return tuple(region for region in regions if lo[list(region)].min() > hi.min()+BASIN_TOLERANCE*W)
