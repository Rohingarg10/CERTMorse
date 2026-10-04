import numpy as np
import pytest
from hypothesis import given, settings, strategies as st
from scipy.optimize import linprog
from certmorse.complex import TorusComplex, lower_star_gradient
from certmorse.controls import tree_cotree_collapse
from certmorse.forman import witness, witness_range, NegativeCycle, is_discrete_morse, difference_arcs
from certmorse.scaling import choose_scale, model_band, cell_band
from certmorse.mip import build_A, solve, solve_B_lazy
from certmorse.mip.cuts import cycle_pairs, cycle_cut, band_cut, satisfied


def make_bounds(g, cx, width=.1):
    s, _ = choose_scale(g-width, g+width)
    lo, hi = model_band(g-width, g+width, s)
    return *cell_band(lo, hi, cx), s


def random_matching(rng, cx, g, arbitrary):
    if not arbitrary:
        return np.concatenate(lower_star_gradient(g, cx))
    y = np.zeros(len(cx.pairs), dtype=np.int8)
    used = set()
    for p in rng.permutation(len(cx.pairs)):
        s, t = map(int, cx.pairs[p])
        if s not in used and t not in used and rng.random() < .65:
            y[p] = 1
            used.update((s, t))
    return y


def test_T26_explicit_collapse():
    cx = TorusComplex(16)
    v = np.arange(cx.nv)
    g = np.cos(4*np.pi*(v%16)/16)+np.cos(2*np.pi*(v//16)/16)-2.5
    lo, hi, _ = make_bounds(g, cx, .01)
    a, b = tree_cotree_collapse(g, cx)
    y = np.concatenate((a,b))
    matched = np.bincount(cx.pairs[y.astype(bool)].ravel(), minlength=cx.nc) > 0
    assert [int(np.sum(~matched[cx.dim == q])) for q in (0,1,2)] == [2,3,1]
    free_lo, free_hi = lo.copy(), hi.copy()
    free_lo[cx.nv:] = lo.min()
    free_hi[cx.nv:] = hi.max()
    x = witness(a, b, free_lo, free_hi, cx)
    assert not isinstance(x, NegativeCycle)
    assert is_discrete_morse(x, a, b, cx)[0]
    assert isinstance(witness(a, b, lo, hi, cx), NegativeCycle)


@settings(max_examples=200, deadline=None, derandomize=True)
@given(st.integers(min_value=0, max_value=2**32-1))
def test_T14_witness_iff_fixed_A(seed):
    cx = TorusComplex(4)
    rng = np.random.default_rng(seed)
    g = rng.integers(-20, 21, cx.nv).astype(float)
    lo, hi, _ = make_bounds(g, cx)
    y = random_matching(rng, cx, g, seed % 2 == 0)
    a, b = cx.split_matching(y)
    x = witness(a, b, lo, hi, cx)
    model = build_A(lo, hi, cx)
    model.fixed_y = dict(enumerate(y))
    r = solve(model, 'cpsat', 5, 8, None, 'results/stage1/fixed-A.log')
    assert r.status in ('OPTIMAL', 'INFEASIBLE')
    assert (r.status == 'OPTIMAL') == (not isinstance(x, NegativeCycle))


def test_T28_100_matchings_against_independent_LP():
    rng = np.random.default_rng(1028)
    feasible = infeasible = 0
    for k in range(100):
        cx = TorusComplex(3+k%2)
        g = rng.normal(size=cx.nv)
        lo, hi, _ = make_bounds(g, cx)
        y = random_matching(rng, cx, g, k%2 == 0)
        a, b = cx.split_matching(y)
        r = witness_range(a, b, lo, hi, cx)
        rows, rhs = [], []
        for u, v, w, _ in difference_arcs(y, lo, hi, cx):
            row = np.zeros(cx.nc)
            if u < cx.nc: row[u] -= 1
            if v < cx.nc: row[v] += 1
            rows.append(row); rhs.append(w)
        if isinstance(r, NegativeCycle):
            lp = linprog(np.zeros(cx.nc), A_ub=rows, b_ub=rhs, bounds=[(None,None)]*cx.nc)
            assert lp.status == 2
            infeasible += 1
            continue
        feasible += 1
        for v in range(cx.nv):
            objective = np.zeros(cx.nc); objective[v] = 1
            for sign, expected in [(1, r[0][v]), (-1, r[1][v])]:
                lp = linprog(sign*objective, A_ub=rows, b_ub=rhs, bounds=[(None,None)]*cx.nc)
                assert lp.success
                assert abs(sign*lp.fun-expected) < 1e-6
    assert feasible >= 40 and infeasible >= 40


def test_T20_signed_cut_preserves_feasible_matchings():
    rng = np.random.default_rng(1020)
    cx = TorusComplex(4)
    families = set()
    for _ in range(50):
        g = rng.normal(size=cx.nv)
        lo, hi, _ = make_bounds(g, cx, 2)
        feasible, cuts = [], []
        for k in range(200):
            y = random_matching(rng, cx, g if k%3 else rng.normal(size=cx.nv), k%2 == 0)
            a, b = cx.split_matching(y)
            cycle = cycle_pairs(y, cx)
            if cycle is not None:
                cuts.append(cycle_cut(cycle)); families.add('cycle')
            else:
                x = witness(a,b,lo,hi,cx)
                if isinstance(x, NegativeCycle):
                    cuts.append(band_cut(x)); families.add('band')
                else:
                    feasible.append(y)
        assert feasible
        optimum=solve(build_A(lo,hi,cx),'cpsat',5,8,None,'results/stage1/cut-optimum.log')
        assert optimum.status=='OPTIMAL'
        feasible.append(optimum.y)
        def check_generated(family,cut,rejected):
            if rejected is not None: assert not satisfied(cut,rejected)
            assert all(satisfied(cut,y) for y in feasible)
        solve_B_lazy(cx,lo,hi,'cpsat',1,8,None,'results/stage1/cut-lazy.log',cut_callback=check_generated)
        assert all(satisfied(cut, y) for cut in cuts for y in feasible)
    assert families == {'cycle','band'}


def test_T10_separated_transfer_and_T15_ties():
    rng = np.random.default_rng(1010)
    cx = TorusComplex(16)
    for k in range(40):
        g = (rng.permutation(cx.nv)*14).astype(float) if k < 20 else rng.integers(0, 4, cx.nv).astype(float)
        # Width of 1000 units, plus required margin, with S = 1.
        lo, hi = cell_band(*model_band(g-500, g+500, 1), cx)
        a, b = lower_star_gradient(g, cx)
        x = witness(a,b,lo,hi,cx)
        assert not isinstance(x, NegativeCycle)
        assert is_discrete_morse(x,a,b,cx)[0]
