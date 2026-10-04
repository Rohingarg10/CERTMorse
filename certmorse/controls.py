"""Explicit tree--cotree collapse, for the T26 regression control only."""
from collections import deque
import numpy as np
from .complex import lower_star_gradient


def tree_cotree_collapse(g, cx):
    ve, _ = lower_star_gradient(g, cx)
    used = {int(e) for _, e in cx.pairs_ve[ve.astype(bool)]}
    dual = [[] for _ in range(cx.nt)]
    for e in range(cx.nv, cx.nv+cx.ne):
        if e in used:
            continue
        a, b = (t-4*cx.nv for t in cx.cofaces[e])
        dual[a].append((b, e))
        dual[b].append((a, e))
    parents = {0: None}
    todo = deque([0])
    while todo:
        a = todo.popleft()
        for b, e in dual[a]:
            if b not in parents:
                parents[b] = e
                todo.append(b)
    if len(parents) != cx.nt:
        raise ValueError('remaining dual graph is disconnected')
    et = np.array([parents[t-4*cx.nv] == e for e, t in cx.pairs_et], dtype=np.int8)
    return ve, et
