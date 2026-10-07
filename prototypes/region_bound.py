"""Region lower bound for band-constrained Forman functions; see docs/METHOD.md.

Minima: for vertex a, C(a) = component containing a of {v : lo_v <= hi_a} (vertex graph).
  Every boundary vertex w has lo_w > hi_a >= min_R hi, so the minimum-x vertex of C(a)
  cannot be matched downward and is critical.
Maxima: for triangle b, D(b) = component containing b of {t : hi_t >= lo_b} (triangles adjacent
  across an edge). Every boundary triangle t' has hi_t' < lo_b <= max_R lo, so the maximum-x
  triangle cannot be matched to an edge and is critical.
Both families are laminar; inclusion-minimal members are pairwise disjoint, so
c0 >= k_min, c2 >= k_max and (Euler) kappa = 2(c0 + c2) >= 2(k_min + k_max).
"""
import sys, numpy as np
sys.path.insert(0, '/mnt/user-data/uploads/CertMorse')
from certmorse.complex import TorusComplex


def _minimal_components(n, adj, member_of):
    comps = set()
    for a in range(n):
        allowed = member_of(a)
        seen = {a}; st = [a]
        while st:
            x = st.pop()
            for y in adj[x]:
                if y not in seen and allowed[y]:
                    seen.add(y); st.append(y)
        comps.add(frozenset(seen))
    comps = list(comps)
    return [c for c in comps if not any(o < c for o in comps)]


def region_bound(cell_lo, cell_hi, cx):
    lo = np.asarray(cell_lo); hi = np.asarray(cell_hi)
    nv, ne = cx.nv, cx.ne
    vadj = [[] for _ in range(nv)]
    for a, b in cx.edge_vertices: vadj[a].append(int(b)); vadj[b].append(int(a))
    vlo, vhi = lo[:nv], hi[:nv]
    kmin = _minimal_components(nv, vadj, lambda a: vlo <= vhi[a])
    # triangles adjacent across an edge
    nt = cx.nt; tlo, thi = lo[4*nv:], hi[4*nv:]
    edge_tris = [[] for _ in range(ne)]
    for t, es in enumerate(cx.tri_edges):
        for e in es: edge_tris[e].append(t)
    tadj = [[] for _ in range(nt)]
    for ts in edge_tris:
        a, b = ts; tadj[a].append(b); tadj[b].append(a)
    kmax = _minimal_components(nt, tadj, lambda b: thi >= tlo[b])
    return 2*(len(kmin)+len(kmax)), len(kmin), len(kmax)


if __name__ == '__main__':
    import glob
    cx = TorusComplex(16)
    print("R8a saved oracle bands (kappa* = 32 = LB_mand = LB_pers = UB_pers on all):")
    for f in sorted(glob.glob('/mnt/user-data/uploads/CertMorse/results/stage1-r8a-v1.7-oracle/*/matching.npz')):
        z = np.load(f)
        print('  ', f.split('/')[-2], 'LB_region =', region_bound(z['cell_lo'], z['cell_hi'], cx))
