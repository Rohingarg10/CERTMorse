"""Numerical checks for claims written into spec v1.6.

A. Uniform coherent offset is a pure gamma-translation for unit weights:
   F_d(g, b) = F_a(g - delta, b); and is NOT for weighted graphs.
B. Certificate transfer: the lower-star gradient of a field whose adjacent scaled
   values differ by >= 13 units, with each vertex >= 13 units inside the (widened)
   band, is realisable as an integer DMF inside the cell band with vertex values pinned.
   Also: show it can FAIL when adjacent values are closer than that.
C. Closure-filtration persistence on the torus: essential classes = (1, 2, 1) only if
   the top dimension is computed; and 2*#positive pairs + #essential <= kappa.
"""
import itertools, heapq
import numpy as np

# ---------------------------------------------------------------- A
def qaoa_F(n, edges, w, gam, bet, offsets):
    N = 2 ** n
    idx = np.arange(N)
    bits = [(idx >> i) & 1 for i in range(n)]
    C = np.zeros(N)
    phase = np.zeros(N)
    for (a, b), we, d in zip(edges, w, offsets):
        zz = 1 - 2 * (bits[a] ^ bits[b])          # Z_a Z_b eigenvalue
        C += we * (1 - zz) / 2
        # RZZ(theta) = exp(-i theta ZZ/2), theta = -gam*we + d
        theta = -gam * we + d
        phase += -theta * zz / 2
    psi = np.exp(1j * phase) / np.sqrt(N)
    # RX(2b) on every qubit = exp(-i b X)
    psi = psi.reshape([2] * n)
    c, s = np.cos(bet), -1j * np.sin(bet)
    U = np.array([[c, s], [s, c]])
    for q in range(n):
        ax = n - 1 - q
        psi = np.moveaxis(np.tensordot(U, np.moveaxis(psi, ax, 0), axes=1), 0, ax)
    p = np.abs(psi.reshape(N)) ** 2
    return -(p @ C)

rng = np.random.default_rng(1)
n = 6
edges = [(0,1),(1,2),(2,0),(2,3),(3,4),(4,5),(5,3),(0,5)]
delta = 0.05
errA_unit = errA_w = 0.0
wts = rng.integers(1, 4, len(edges))
for _ in range(50):
    g, b = rng.uniform(0, 2*np.pi), rng.uniform(0, np.pi)
    u = np.ones(len(edges), int)
    errA_unit = max(errA_unit, abs(qaoa_F(n, edges, u, g, b, [delta]*len(edges)) - qaoa_F(n, edges, u, g - delta, b, [0]*len(edges))))
    errA_w = max(errA_w, abs(qaoa_F(n, edges, wts, g, b, [delta]*len(edges)) - qaoa_F(n, edges, wts, g - delta, b, [0]*len(edges))))
per = max(abs(qaoa_F(n, edges, wts, g, b, rng.uniform(-.1,.1,len(edges))*0+0.07) - qaoa_F(n, edges, wts, g + 2*np.pi, b, [0.07]*len(edges)))
          for g, b in rng.uniform(0, 3, (20, 2)))
print(f"A. unit weights: max|F_d(g,b) - F_a(g-d,b)| = {errA_unit:.2e}   (expect ~1e-15)")
print(f"A. weighted:     max|F_d(g,b) - F_a(g-d,b)| = {errA_w:.2e}   (expect clearly nonzero)")
print(f"A. weighted, offset, 2pi-periodic in gamma: max err = {per:.2e}")

# ---------------------------------------------------------------- complex
def build(m):
    vid = lambda i, j: (i % m) + m * (j % m)
    nV = m*m
    edges = []
    for j in range(m):
        for i in range(m):
            v = vid(i,j); edges += [(v, vid(i+1,j)), (v, vid(i,j+1)), (v, vid(i+1,j+1))]
    tris = []
    for j in range(m):
        for i in range(m):
            v = vid(i,j)
            tris += [(3*v, 3*v+2, 3*vid(i+1,j)+1), (3*v+2, 3*v+1, 3*vid(i,j+1))]
    nE, nT = len(edges), len(tris)
    E0, T0 = nV, nV+nE
    faces = {}       # cell -> list of codim-1 faces (global ids)
    for e,(a,b) in enumerate(edges): faces[E0+e] = [a, b]
    for t, es in enumerate(tris): faces[T0+t] = [E0+e for e in es]
    for v in range(nV): faces[v] = []
    cof = {c: [] for c in range(nV+nE+nT)}
    for c, fs in faces.items():
        for f in fs: cof[f].append(c)
    verts = {}
    for v in range(nV): verts[v] = (v,)
    for e,(a,b) in enumerate(edges): verts[E0+e] = (a,b)
    for t, es in enumerate(tris):
        verts[T0+t] = tuple(sorted(set(edges[es[0]]) | set(edges[es[1]]) | set(edges[es[2]])))
    dim = {c: (0 if c < E0 else 1 if c < T0 else 2) for c in faces}
    return dict(m=m, nV=nV, nC=nV+nE+nT, faces=faces, cof=cof, verts=verts, dim=dim, E0=E0, T0=T0)

def lower_star_gradient(cx, val):
    """Robins-Wood-Sheppard ProcessLowerStars, ties by vertex index (SoS)."""
    nV = cx['nV']
    order = sorted(range(nV), key=lambda v: (val[v], v))
    rank = np.empty(nV, int); rank[order] = np.arange(nV)
    key = lambda c: tuple(sorted((rank[v] for v in cx['verts'][c]), reverse=True))
    owner = lambda c: max(cx['verts'][c], key=lambda v: rank[v])
    pair = {}; crit = set()
    for v in order:
        L = [c for c in itertools.chain(cx['cof'][v], *[cx['cof'][e] for e in cx['cof'][v]]) if owner(c) == v]
        L = list(dict.fromkeys(L))
        if not L:
            crit.add(v); continue
        Ls = set(L)
        edgesL = [c for c in L if cx['dim'][c] == 1]
        delta = min(edgesL, key=key)
        pair[v] = delta; pair[delta] = v
        classified = {delta}
        def unpaired_faces(a):
            return [f for f in cx['faces'][a] if f in Ls and f not in classified]
        PQ1 = [(key(e), e) for e in edgesL if e != delta]; heapq.heapify(PQ1)
        PQ0 = []
        for a in cx['cof'][delta]:
            if a in Ls and len(unpaired_faces(a)) == 1: heapq.heappush(PQ0, (key(a), a))
        while PQ1 or PQ0:
            while PQ0:
                _, a = heapq.heappop(PQ0)
                if a in classified: continue
                uf = unpaired_faces(a)
                if len(uf) == 0:
                    heapq.heappush(PQ1, (key(a), a))
                else:
                    f = uf[0]
                    pair[a] = f; pair[f] = a; classified.update((a, f))
                    for z in itertools.chain(cx['cof'][a], cx['cof'][f]):
                        if z in Ls and z not in classified and len(unpaired_faces(z)) == 1:
                            heapq.heappush(PQ0, (key(z), z))
            while PQ1:
                _, g = heapq.heappop(PQ1)
                if g in classified: continue
                crit.add(g); classified.add(g)
                for z in cx['cof'][g]:
                    if z in Ls and z not in classified and len(unpaired_faces(z)) == 1:
                        heapq.heappush(PQ0, (key(z), z))
                break
    return pair, crit

def witness(cx, pair, lo, hi):
    """Bellman-Ford on the difference system. Returns x or None (negative cycle)."""
    nC = cx['nC']; S = nC
    arcs = []   # x_b - x_a <= w  ->  arc a->b weight w
    for t in range(nC):
        for s in cx['faces'][t]:
            if pair.get(s) == t:   arcs.append((s, t, 0))      # x_t <= x_s
            else:                  arcs.append((t, s, -1))     # x_s <= x_t - 1
    for c in range(nC):
        arcs.append((S, c, hi[c])); arcs.append((c, S, -lo[c]))
    d = np.full(nC+1, np.inf); d[S] = 0
    for it in range(nC+1):
        ch = False
        for a, b, w in arcs:
            if d[a] + w < d[b]: d[b] = d[a] + w; ch = True
        if not ch: break
    else:
        return None
    for a, b, w in arcs:
        if d[a] + w < d[b]: return None
    x = d[:nC] - d[S]
    return x

def cell_band(cx, vlo, vhi):
    lo = np.empty(cx['nC']); hi = np.empty(cx['nC'])
    for c in range(cx['nC']):
        vs = cx['verts'][c]
        lo[c] = max(vlo[v] for v in vs); hi[c] = max(vhi[v] for v in vs)
    return lo, hi

def kappa(cx, pair): return cx['nC'] - len(pair)

# ---------------------------------------------------------------- B
m = 8
cx = build(m)
def field(kind, i, j):
    g, b = 2*np.pi*i/m, np.pi*j/m
    if kind == 'perfect': return np.cos(g) + np.cos(2*b)
    if kind == 'T5':      return np.cos(2*g) + np.cos(2*b)
for kind, expect in (('perfect', 4), ('T5', 8)):
    val = np.array([field(kind, v % m, v // m) for v in range(cx['nV'])])
    pair, crit = lower_star_gradient(cx, val)
    print(f"B. lower-star kappa on {kind:7s} field at m={m}: {kappa(cx, pair)} (expect {expect})")

ok_sep = fail_sep = tried_close = 0
for trial in range(40):
    r = np.random.default_rng(100 + trial)
    # random field with enforced adjacent separation: random permutation scaled by 14 units
    perm = r.permutation(cx['nV'])
    a = perm * 14                                    # all values distinct by >= 14 units
    pair, _ = lower_star_gradient(cx, a)
    vlo, vhi = a - 13, a + 13                        # widened band, a_v exactly 13 inside
    lo, hi = cell_band(cx, vlo, vhi)
    lo[:cx['nV']] = a; hi[:cx['nV']] = a             # pin vertex values to the truth
    x = witness(cx, pair, lo, hi)
    ok_sep += x is not None
    # now values separated by only 1 unit
    a2 = perm * 1
    pair2, _ = lower_star_gradient(cx, a2)
    lo2, hi2 = cell_band(cx, a2 - 13, a2 + 13); lo2[:cx['nV']] = a2; hi2[:cx['nV']] = a2
    x2 = witness(cx, pair2, lo2, hi2)
    fail_sep += x2 is None; tried_close += 1
print(f"B. separation 14, margin 13, vertices pinned: realisable in {ok_sep}/40 random fields (expect 40)")
print(f"B. separation 1,  margin 13, vertices pinned: NOT realisable in {fail_sep}/{tried_close} (shows the condition matters)")

# ---------------------------------------------------------------- C
def persistence_z2(cx, vals, top=True):
    nC = cx['nC']
    phi = np.array([min([vals[c]] + [vals[z] for z in up_closure(cx, c)]) for c in range(nC)])
    order = sorted(range(nC), key=lambda c: (phi[c], cx['dim'][c], c))
    pos = {c: k for k, c in enumerate(order)}
    cols = [set(pos[f] for f in cx['faces'][c]) for c in order]
    low_of = {}; pairs = []; paired = set()
    for j in range(nC):
        col = cols[j]
        while col:
            l = max(col)
            if l in low_of: col ^= cols[low_of[l]]
            else: break
        if col:
            l = max(col); low_of[l] = j; pairs.append((l, j)); paired.update((l, j))
    ess = [order[k] for k in range(nC) if k not in paired]
    dims = [cx['dim'][c] for c in ess]
    if not top: dims = [d for d in dims if d < 2]
    pos_pairs = sum(1 for (i, j) in pairs if phi[order[j]] > phi[order[i]])
    return sorted(dims), pos_pairs

_upc = {}
def up_closure(cx, c):
    if c not in _upc:
        s = set(); st = [c]
        while st:
            z = st.pop()
            for y in cx['cof'][z]:
                if y not in s: s.add(y); st.append(y)
        _upc[c] = s
    return _upc[c]

m = 6; cx = build(m); _upc.clear()
val = np.array([np.cos(2*np.pi*(v % m)/m*2) + np.cos(np.pi*(v//m)/m*2) for v in range(cx['nV'])]) * 1000
val += np.random.default_rng(3).uniform(-1, 1, cx['nV'])
pair, _ = lower_star_gradient(cx, val)
lo, hi = cell_band(cx, np.round(val) - 500, np.round(val) + 500)
x = witness(cx, pair, lo, hi)
k = kappa(cx, pair)
ess_top, posp = persistence_z2(cx, x, top=True)
ess_no, _ = persistence_z2(cx, x, top=False)
print(f"C. essential dims with top dim: {ess_top} (expect [0,1,1,2]); without: {ess_no}")
print(f"C. 2*#positive pairs + #essential = {2*posp + len(ess_top)} <= kappa = {k}")
