"""Check: does Formulation A with free edge/triangle values collapse all maxima?

Builds the CERTMORSE torus complex and Formulation A described in docs/METHOD.md,
and solves on a narrow band around g = cos(2*gamma) + cos(2*beta) (2 min, 2 max, 4 saddles,
kappa_true = 8) under two auxiliary-cell bound regimes:
  (free)  edges/triangles in [-SW, 2]           -- unconstrained cell extension
  (cell)  edges/triangles in [max l_v, max u_v] -- proposed cell band
Prediction from the tree-cotree argument: free -> 2*c0 + 2 = 6; cell -> 8.
"""
import sys
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import lil_matrix

m = int(sys.argv[1]) if len(sys.argv) > 1 else 8
half = int(sys.argv[2]) if len(sys.argv) > 2 else 40   # half-width of band, scaled units

def vid(i, j): return (i % m) + m * (j % m)
nV = m * m
edges, tris = [], []
for j in range(m):
    for i in range(m):
        v = vid(i, j); r = vid(i+1, j); u = vid(i, j+1); d = vid(i+1, j+1)
        edges += [(v, r), (v, u), (v, d)]
for j in range(m):
    for i in range(m):
        v = vid(i, j)
        e0 = 3*v; e1 = 3*v+1; e2 = 3*v+2
        e1r = 3*vid(i+1, j) + 1
        e0u = 3*vid(i, j+1) + 0
        tris += [(e0, e2, e1r), (e2, e1, e0u)]
nE, nT = len(edges), len(tris)
assert nE == 3*nV and nT == 2*nV
# global cell index
E0, T0 = nV, nV + nE
nC = nV + nE + nT
pairs = []
for e, (a, b) in enumerate(edges):
    pairs += [(a, E0+e), (b, E0+e)]
for t, es in enumerate(tris):
    for e in es:
        pairs.append((E0+e, T0+t))
nP = len(pairs)
assert nP == 12 * nV

# field and band (scaled integers)
S = 100
g = np.zeros(nV)
for j in range(m):
    for i in range(m):
        gam, bet = 2*np.pi*i/m, np.pi*j/m
        g[vid(i, j)] = np.cos(2*gam) + np.cos(2*bet) - 2.5
# break exact ties deterministically so the "truth" is generic, then band around it
rng = np.random.default_rng(0)
mid = np.round(S * g + rng.uniform(-3, 3, nV)).astype(int)
lo, hi = mid - half, mid + half
W = 5.0
SW = int(S * W)

verts_of = []
for e,(a,b) in enumerate(edges): verts_of.append((a,b))
tri_verts = []
for t, es in enumerate(tris):
    vs = set()
    for e in es: vs.update(edges[e])
    tri_verts.append(tuple(vs))

def solve(mode):
    nvar = nC + nP
    lb = np.empty(nvar); ub = np.empty(nvar)
    lb[:nV], ub[:nV] = lo, hi
    for e in range(nE):
        a, b = edges[e]
        if mode == "free":
            lb[E0+e], ub[E0+e] = -SW, 2
        else:
            lb[E0+e], ub[E0+e] = max(lo[a], lo[b]), max(hi[a], hi[b])
    for t in range(nT):
        vs = tri_verts[t]
        if mode == "free":
            lb[T0+t], ub[T0+t] = -SW, 2
        else:
            lb[T0+t], ub[T0+t] = max(lo[v] for v in vs), max(hi[v] for v in vs)
    lb[nC:], ub[nC:] = 0, 1
    M = SW + 3
    A = lil_matrix((2*nP + nC, nvar)); cl = []; cu = []
    r = 0
    for p, (s, t) in enumerate(pairs):
        # matched: x_t - x_s - M(1-y) <= 0  ->  x_t - x_s + M y <= M
        A[r, t] = 1; A[r, s] = -1; A[r, nC+p] = M; cl.append(-np.inf); cu.append(M); r += 1
        # unmatched: x_s - x_t - M y <= -1
        A[r, s] = 1; A[r, t] = -1; A[r, nC+p] = -M; cl.append(-np.inf); cu.append(-1); r += 1
    for p, (s, t) in enumerate(pairs):
        A[r + s, nC+p] = 1; A[r + t, nC+p] = 1
    cl += [-np.inf]*nC; cu += [1]*nC
    c = np.zeros(nvar); c[nC:] = -1
    res = milp(c, constraints=LinearConstraint(A.tocsr(), cl, cu),
               integrality=np.ones(nvar), bounds=Bounds(lb, ub),
               options={"time_limit": 280, "mip_rel_gap": 0})
    if res.x is None: return res.status, res.message, None, None
    y = np.round(res.x[nC:]).astype(int)
    matched = set()
    for p, (s, t) in enumerate(pairs):
        if y[p]: matched.update((s, t))
    crit = [cc for cc in range(nC) if cc not in matched]
    c0 = sum(1 for cc in crit if cc < E0)
    c1 = sum(1 for cc in crit if E0 <= cc < T0)
    c2 = sum(1 for cc in crit if cc >= T0)
    return res.status, res.message, nC - 2*int(y.sum()), (c0, c1, c2)

for mode in ("free", "cell"):
    st, msg, kappa, cs = solve(mode)
    print(f"m={m} half={half} mode={mode:5s} status={st} kappa*={kappa} (c0,c1,c2)={cs}  [{msg[:40]}]")
