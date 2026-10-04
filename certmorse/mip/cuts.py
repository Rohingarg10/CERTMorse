"""Two distinct valid cut families from Appendix A.4."""
import numpy as np


def all_cycle_pairs(y, cx, limit=32):
    adj = [[] for _ in range(cx.nc)]
    for p, (s, t) in enumerate(cx.pairs):
        a, b = (int(s), int(t)) if y[p] else (int(t), int(s))
        adj[a].append((b, p))
    color = np.zeros(cx.nc, dtype=np.int8)
    parent = [None]*cx.nc
    cycles, seen = [], set()
    for root in range(cx.nc):
        if color[root]:
            continue
        color[root] = 1
        stack = [(root, iter(adj[root]))]
        while stack:
            u, edges = stack[-1]
            try:
                v, p = next(edges)
            except StopIteration:
                color[u] = 2
                stack.pop()
                continue
            if color[v] == 0:
                parent[v] = (u, p)
                color[v] = 1
                stack.append((v, iter(adj[v])))
            elif color[v] == 1:
                pairs, cursor = [p], u
                while cursor != v:
                    cursor, edge = parent[cursor]
                    pairs.append(edge)
                matched = tuple(sorted(p for p in pairs if y[p]))
                if matched not in seen:
                    seen.add(matched); cycles.append(list(matched))
                    if len(cycles)>=limit: return cycles
    return cycles


def cycle_pairs(y, cx):
    cycles = all_cycle_pairs(y,cx,1)
    return cycles[0] if cycles else None


def band_cycles(y, lo, hi, cx, limit=16):
    """Find additional valid conflicts by removing previously used arcs.

    Every reported negative cycle exists in the original difference graph;
    removal searches subgraphs and never changes an arc's direction/weight.
    """
    from ..forman import difference_arcs, _bellman, NegativeCycle
    arcs = difference_arcs(y,lo,hi,cx)
    cycles=[]
    for _ in range(limit):
        conflict = _bellman(cx.nc+1,arcs,cx.nc,y)
        if not isinstance(conflict,NegativeCycle): break
        cycles.append(conflict)
        pairs = conflict.pairs_plus+conflict.pairs_minus
        if not pairs: break
        removed = pairs[0]
        arcs = [arc for arc in arcs if arc[3]!=removed]
    return cycles


def cycle_cut(pairs):
    return ({p: 1 for p in pairs}, None, len(pairs)-1)


def band_cut(negative_cycle):
    terms = {p: -1 for p in negative_cycle.pairs_plus}
    terms.update({p: 1 for p in negative_cycle.pairs_minus})
    return terms, 1-len(negative_cycle.pairs_plus), None


def satisfied(cut, y):
    terms, lo, hi = cut
    value = sum(c*int(y[p]) for p, c in terms.items())
    return (lo is None or value >= lo) and (hi is None or value <= hi)
