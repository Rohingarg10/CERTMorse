"""Exact matching/value validation and Bellman--Ford certificates."""
from dataclasses import dataclass
import numpy as np


@dataclass
class NegativeCycle:
    nodes: list[int]
    pairs_plus: list[int]
    pairs_minus: list[int]
    reason: str = "negative cycle"


def _matching(match_ve, match_et, cx):
    y = np.concatenate((np.asarray(match_ve), np.asarray(match_et)))
    if y.shape != (len(cx.pairs),) or not np.all((y == 0) | (y == 1)):
        raise ValueError("invalid binary matching")
    use = np.bincount(cx.pairs[y.astype(bool)].ravel(), minlength=cx.nc)
    if np.any(use > 1):
        raise ValueError("cell belongs to multiple matched pairs")
    return y.astype(np.int8)


def difference_arcs(y, lo, hi, cx):
    source = cx.nc
    arcs = []
    for p, (s, t) in enumerate(cx.pairs):
        arcs.append((int(s), int(t), 0, p) if y[p] else (int(t), int(s), -1, p))
    for c in range(cx.nc):
        arcs.extend(((source, c, int(hi[c]), -1), (c, source, -int(lo[c]), -1)))
    return arcs


def _bellman(n, arcs, source, y):
    # Python integer arithmetic; None is infinity, never a floating-point sentinel.
    dist, pred = [None] * n, [None] * n
    dist[source] = 0
    last = None
    for _ in range(n):
        last = None
        for a, b, w, p in arcs:
            if dist[a] is not None and (dist[b] is None or dist[b] > dist[a] + w):
                dist[b] = dist[a] + w
                pred[b] = (a, p)
                last = b
        if last is None:
            return dist
    v = last
    for _ in range(n):
        v = pred[v][0]
    start, nodes, ps = v, [], set()
    while True:
        nodes.append(v)
        a, p = pred[v]
        if p >= 0:
            ps.add(p)
        v = a
        if v == start:
            break
    return NegativeCycle(nodes, sorted(p for p in ps if y[p]), sorted(p for p in ps if not y[p]))


def witness(match_ve, match_et, cell_lo, cell_hi, cx):
    y = _matching(match_ve, match_et, cx)
    lo, hi = np.asarray(cell_lo), np.asarray(cell_hi)
    if lo.shape != (cx.nc,) or hi.shape != (cx.nc,) or lo.dtype.kind not in 'iu' or hi.dtype.kind not in 'iu':
        raise ValueError("integer bounds required for every cell")
    if np.any(lo > hi):
        raise ValueError("empty cell band")
    result = _bellman(cx.nc+1, difference_arcs(y, lo, hi, cx), cx.nc, y)
    if isinstance(result, NegativeCycle):
        return result
    return np.array([d-result[cx.nc] for d in result[:cx.nc]], dtype=np.int64)


def witness_range(match_ve, match_et, cell_lo, cell_hi, cx):
    y = _matching(match_ve, match_et, cx)
    arcs = difference_arcs(y, cell_lo, cell_hi, cx)
    upper = _bellman(cx.nc+1, arcs, cx.nc, y)
    if isinstance(upper, NegativeCycle):
        return upper
    backward = _bellman(cx.nc+1, [(b,a,w,p) for a,b,w,p in arcs], cx.nc, y)
    if isinstance(backward, NegativeCycle):
        return backward
    return (np.array([-d for d in backward[:cx.nv]], dtype=np.int64),
            np.array(upper[:cx.nv], dtype=np.int64))


def is_discrete_morse(x_cell, match_ve, match_et, cx):
    try:
        y = _matching(match_ve, match_et, cx)
    except ValueError as exc:
        return False, {"reason": str(exc)}
    x = np.asarray(x_cell)
    if x.shape != (cx.nc,) or x.dtype.kind not in 'iu':
        return False, {"reason": "integer cell values required"}
    s, t = cx.pairs.T
    good = np.where(y, x[t] <= x[s], x[s] < x[t])
    if not np.all(good):
        p = int(np.flatnonzero(~good)[0])
        return False, {"pair": p, "cells": cx.pairs[p].tolist(), "reason": "value inequality"}
    # Reversed Hasse diagram: matched arcs go up; every other incidence goes down.
    adj = [[] for _ in range(cx.nc)]
    indeg = np.zeros(cx.nc, dtype=np.int64)
    for p, (a,b) in enumerate(cx.pairs):
        a,b = (int(a),int(b)) if y[p] else (int(b),int(a))
        adj[a].append(b)
        indeg[b] += 1
    stack = list(np.flatnonzero(indeg == 0))
    count = 0
    while stack:
        a = stack.pop()
        count += 1
        for b in adj[a]:
            indeg[b] -= 1
            if indeg[b] == 0:
                stack.append(b)
    if count != cx.nc:
        return False, {"reason": "cycle", "cells": np.flatnonzero(indeg).tolist()}
    return True, {}
