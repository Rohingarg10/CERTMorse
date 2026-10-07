# CERTMORSE method and Stage 1 verification contract

This public description governs interpretation of the released Stage 1 method.
[STAGE1.md](STAGE1.md) is the measurement record and [CERTIFICATE.md](CERTIFICATE.md)
states the certificate boundaries. Historical version and section labels in code
and evidence identify the rules under which those records were produced; they do
not require access to private working documents. Stage 1 is complete at `v0.1`;
Stage 2 is planned. No optimizer-success prediction was measured.

## 1. Landscape, grid and reported band

An instance is an integer-weight MaxCut graph with at most ten vertices. With
`W = sum(edge weights)` and `C = sum(w_ij (1-Z_i Z_j)/2)`, the minimized field is
`F(gamma,beta) = -<C>`, in `[-W,0]`. The depth-one circuit applies Hadamards,
`RZZ(-gamma*w_ij + offset_ij)` in committed edge order, and `RX(2*beta)`.
Graph vertex i is little-endian qubit i. Realized graphs, weights and coherent
offsets are fixed inputs in [instances.yaml](../configs/instances.yaml).

Channels are ideal (a); depolarizing noise on sx/x at 0.001 and cx at 0.01 (b);
amplitude damping 0.01 on sx/x and its tensor product on cx (c); fixed additive
per-edge RZZ offsets (d); uniform additive offset 0.05 (d0); and b plus d (e).
Noise is attached after transpilation to `rz,sx,x,cx`. Shot-free statevector or
density-matrix probabilities give exact means and variances for that channel.
Exact here means without shot sampling, including any channel noise.

Gamma has period 2π. The ordinary beta domain has period π for c and π/2 for
a, b, d, d0 and e. QAOA vertex `(i,j)` is at
`gamma = 2π(i+1/4)/m`, `beta = P_beta(j+1/4)/m`. Synthetic fixtures retain their
original unshifted beta-π grid. Cross-channel comparisons use a common beta-π
domain when declared. Domain periods and measured symmetries are explicit
metadata; counts use the whole applicable torus.

All indices are modulo m. A square with vertices v, right(v), up(v), diag(v)
is split into `(v,right,diag)` and `(v,diag,up)`. There are m² vertices, 3m²
edges, 2m² triangles, 6m² cells and 12m² codimension-one incidences. Global
indices place vertices first, edges next and triangles last. Vertex adjacency
has six neighbours: right, left, up, down, northeast and southwest. The smallest
supported simplicial torus has m=3.

Independent bounded shots produce a mean Fhat and vertex band `[ell_v,u_v]`.
At N_v shots and simultaneous error budget alpha_eff, the Hoeffding half-width is
`W sqrt(log(2*m²/alpha_eff)/(2*N_v))`. Oracle mode uses
`Phi^-1(1-alpha_eff/(2*m²)) sqrt(Var_exact/N_v)`; empirical mode substitutes
sample variance, falling back to Hoeffding at zero variance or N_v<30.
Half-widths have floor `1e-4*W`, and endpoints are clipped to `[-W,0]`.
Hoeffding provides the stated simultaneous finite-sample guarantee. Oracle and
empirical Gaussian coverage are approximations, even with known variance.
The reported band is retained separately from all model widening and margins.

## 2. Optimization, witnesses and count certificates

A cell-valued Forman discrete Morse function has at most one coface whose value
is no greater than its value and at most one face whose value is no smaller.
The exceptional incidences form its acyclic matching. Unmatched cells are
critical. If y is the incidence matching, `kappa = 6m² - 2 sum(y)`.

The cell band for edge or triangle c is
`[max_{v in c} ell_v, max_{v in c} u_v]`. Free higher-dimensional values would
change the optimization problem and are forbidden. The problem minimizes
critical cells over band-feasible discrete Morse functions.

Computation chooses the smallest power-of-ten scale S giving minimum full width
at least 1000 integer units, capped at 10^7. If needed, narrow intervals are
symmetrically widened to 1000/S. Add 14/S outward to both sides, then round lower
endpoints up and upper endpoints down. Integer cell bounds `lo,hi` are maxima of
the integer vertex endpoints. These changes are recorded and do not replace the
reported statistical band.

Formulation A uses bounded integer cell potentials x and binary incidence
matches y, maximizing sum(y). At most one match touches each cell. For face s
and coface t, a match requires `x_t <= x_s`; an unmatched incidence requires
`x_s <= x_t-1`. These inequalities preclude a closed gradient path. A midpoint
lower-star matching supplies an independently checked feasible fallback.

Formulation B uses match variables and separates both gradient cycles and
band-infeasible candidates. For a matched cycle Q, `sum_Q y <= |Q|-1` is valid.
For a signed band conflict, matched Q+ and unmatched Q- require
`sum_Q+ (1-y) + sum_Q- y >= 1`; dropping its unmatched terms is invalid.
The complete witness is integer Bellman–Ford on all cells plus a source,
including both bounds on every cell and all matched/unmatched inequalities.
A negative cycle rejects the candidate. A feasible witness is checked again
by the discrete-Morse validator and original model bounds.

For a CP-SAT upper bound B on the maximum match count,
`kappa_lb = 6m² - 2 floor(B)` is a count lower bound, including at timeout.
Only OPTIMAL supplies `kappa_star`. A witness certifies feasibility, not
optimality. HiGHS bounds are numerical comparisons; its qualified representation
uses exact endpoint compression, continuous internal potentials, binary matches,
per-incidence big-M rows and an original-unit integer witness.

On the torus, critical counts satisfy `c0>=1`, `c1>=2`, `c2>=1`, and
`c0-c1+c2=0`. Hence `kappa = 2(c0+c2)>=4` and is even. A covered true field's
lower-star matching transfers to the integer band when adjacent true values
are separated by at least 14/S. The 14-unit outward margin leaves at least 13
units around each rounded true vertex value. Each lower star has at most 13
cells; an acyclic ordering assigns offsets 0 through 12, satisfying its
incidence inequalities. Between stars, separation gives strict increase.
This yields a band-feasible true matching. A direct exact witness can verify
transfer even without this sufficient separation condition. Under coverage and
transfer, `kappa_cert <= kappa_star <= kappa_true`.

## 3. Region bound and valid rows

Using integer model endpoints, let C(a) be the six-neighbour component of
vertex a in `{v:lo_v<=hi_a}`. Let D(b) be the edge-sharing triangle component
of triangle b in `{t:hi_t>=lo_b}`. Each family is laminar: overlapping
threshold components are nested. Deduplicate and retain inclusion-minimal
components. They are pairwise disjoint within each dimension; their counts
are k_min and k_max.

A smallest-valued vertex inside C(a) has value at most `hi_a`. Every boundary
vertex has value greater than `hi_a`. If the selected vertex were matched to
an edge, its other endpoint would have strictly smaller value, impossible
inside the component or on its boundary. Thus every C(a) contains a critical
vertex. Dually, a largest-valued triangle in D(b) has value at least `lo_b`;
every boundary triangle has value below `lo_b`. A matched triangle would have
a strictly larger triangle across its matched edge, also impossible. Thus
every D(b) contains a critical triangle.

Disjointness and Euler therefore give
`LB_region = 2(k_min+k_max) <= kappa` for every feasible matching. Region rows
require at least one unmatched cell per minimal component. Morse rows impose
the torus critical-count inequalities. Substituting matching counts into Euler
cancels every match variable and leaves the fixed Euler characteristic zero.
These rows exclude no feasible matching; summing them gives the region count
bound already in the relaxation. The certified lower bound is
`max(CP-SAT kappa_lb, LB_region)`. Region-bound tightness is not guaranteed.
All seven saved equality-target probes returned UNKNOWN at 1800 s with unchanged
bounds; whether LB_region is exact on those bands remains unresolved.

## 4. Basin score, persistence and resolution

A vertex matched to edge `(v,w)` flows to w; a critical vertex terminates flow.
Witness inequalities make every vertex step strictly decreasing. These flows
partition m² equal-area vertices into combinatorial basins. They are not
classical optimizer attraction basins.

For depth field H and basin B_k, `d_k=min_{v in B_k} H_v`. With
`tau_min=0.02*W`, P is the fraction of vertices in basins whose depth is within
tau_min of the smallest basin depth. Use shot means for observed matching
scores and the true field for reference scores, independently of witness
potentials. P describes a selected simplest consistent landscape and is an
estimate to compare with resolution-adjusted true flow probability P0_res.
It is never a certificate and does not estimate P0 when relevant minima are
unresolved. Neither the count theorem nor Stage 1 establishes optimizer-success
prediction.

P0 applies the depth rule to the true lower-star matching. Compute H0
persistence on the six-neighbour graph in `(value,index)` order with union-find
and the elder rule; the essential minimum has infinite persistence. Starting
from true basin labels, merge younger representatives with persistence below
a threshold into their elder representatives in merge-height order. P0_res is
the area whose resulting representative lies within tau_min of the true
minimum. `P0_res(0)=P0` and `P0_res(infinity)=1`.

Full band widths are `w_max=max(u-ell)` and `w_med=median(u-ell)`.
Reported `P0_res` uses w_med; `P0_res_guaranteed` uses 2*w_max. The CSV field
`resolution=2*w_max` is the sufficient visibility threshold, not grid spacing
or a prediction-error bound. The median-width convention is not the theorem's
threshold. `P_possible_simplest` uses `min_B ell <= min_v u + tau_min` on the
selected matching. Since `ell<=H<=u`, P is no greater than this score. It is
withdrawn as an ambiguity measure because it cannot recover erased basins.

Sampling is restricted to proved optima, excludes previously seen vertex–edge
matchings and uses secondary random weights. Medians describe that procedure;
ranges are observed unless enumeration is exhausted. The first ten OPTIMAL
bands are selected, excluding timeouts. Time-capped incumbents have separately
labelled non-optimal counts and scores. W8a oracle found only 1–2 optima per
band before every 300 s cap, so its within-band spread is unmeasured. An
OPTIMAL kappa=4 implies one minimum and P=1 by construction; these trivial
bands are kept separate.

## 5. Visibility proposition and certified traps

Let G be the true vertex field, `ell<=G<=u` a covering reported band, and
`w=max_v(u_v-ell_v)` its maximum full width, before model margins. Let C(a)
now mean a's component in `{v:ell_v<=u_a}`. Its inclusion-minimal components
are **reported-band** minimum regions, distinct from integer model regions.
A **certified trap** is a minimal region M satisfying
`min_{v in M} ell_v > min_v u_v + tau_min`. The count `n_traps_cert` is
conditional on coverage. Hoeffding supplies the stated simultaneous guarantee;
oracle Gaussian coverage remains approximate.

**Proposition.**

1. Every minimum a of G with H0 persistence greater than 2w has a minimal
   reported-band region in its own unmerged neighbourhood. Distinct such minima
   have disjoint regions, so their number is at most k_min.
2. Every certified trap contains a non-global local minimum of G with value
   greater than `min G + tau_min`. One trap proves P0<1 for true discrete flow.
3. A minimum a in (1) whose depth gap exceeds `2w+tau_min` yields a certified trap.

**Proof.** Coverage and full width imply `ell_v>=G_v-w` and `u_v<=G_v+w`.
For (1), let K(a) be a's component in `{v:G_v<=G(a)+2w}`. Persistence greater
than 2w means it has not met an older minimum, and its minimum value is G(a).
If `ell_v<=u_a`, the endpoint inequalities imply `G_v<=G(a)+2w`, hence
`C(a) subset K(a)`. The finite laminar family within C(a) contains a minimal
region M_a. If K(a) and K(b) intersect, the lower-threshold component lies
inside the higher-threshold one. An older minimum would then occur in the
younger component before its persistence threshold, a contradiction. The elder
ordering handles equal birth values. Thus the regions are disjoint.

For (2), write `M=C(b)` and choose c minimizing G on M. Every boundary vertex
x satisfies `G_x>=ell_x>u_b>=G_b>=G_c`. A local minimum lies inside M, strict
for the tie-free fields used here; tied fields use the fixed lower-star rule.
Its value is `G_c>=min_M ell>min u+tau_min>=min G+tau_min`. Its positive-area
basin lies outside the successful class, so P0<1.

For (3), `min_M_a ell>=min_K(a) G-w=G(a)-w`, while `min u<=min G+w`.
The assumed depth gap makes their difference greater than tau_min, precisely
the certified-trap condition. ∎

The result supplies sufficient visibility and non-globality under coverage.
It asserts neither equality of P with P0_res nor location of optimizer
attractors. In Stage 1, R8a minima with persistence about 1.57–1.69 lie above
oracle resolution 1.11 and below Hoeffding resolution 3.26, consistent with
kappa_star changing from 10–12 to 16=kappa_true. E8a retains kappa_star=8;
two unresolved dimples and their saddles account for its four missing cells,
with P=P0_res=1 and P0 about 0.508. W8a oracle certifies 2–4 traps but fails
the m=16 grid adequacy check, so no basin-prediction conclusion is drawn.

## 6. Persistence convention and grid adequacy

Cell-function persistence uses the face-monotone closure
`phi(c)=min_{rho containing c} f(rho)`, including c. It equals ordinary
lower-star filtration for `f(c)=max_{v in c} F(v)`. Monotonicity is asserted,
not silently repaired. GUDHI uses mod-two coefficients, zero minimum
persistence and the maximal dimension. Bottleneck distance is the maximum of
the three dimensionwise exact comparisons, including infinite essential bars.

Simulation-only grid adequacy compares depth-based global classification of
grid basins with continuously refined minima under the same tolerance.
A selected grid size must pass along with every larger tested size. Recorded
choices are E8a 16, E8b 16, W8a 32, W8b 48 and R8a 16. W8a at 16 fails.
These checks do not supply a continuum topology certificate.

## 7. Gate and evidence rules

The original six-item gate requires:

1. Every Stage 1 test ID T1–T39 except Stage 2 IDs T12, T13 and T18, with no
   required integration skips; specifically T36–T39 pass, preserved T37
   interruption evidence passes, and independent agreement, witness, valid-row,
   transfer and resolution checks pass.
2. Exact re-scoring of all 80 earlier bands from saved arrays, including T38
   and saved sampling checks.
3. The completion evidence for 40 new oracle counts (E8a 20/20 and W8a 10/20
   OPTIMAL), all 60 oracle bands and 30 sampling runs totalling 411 optima.
4. Records and unchanged configurations for all seven 1800 s probes, with
   their UNKNOWN outcomes and unchanged bounds verified.
5. Updated STAGE1 and CERTIFICATE text checked against saved fields, including
   the visibility proof, trap definition, sampling and selection limits.
6. The scientific source digest recomputed from the committed tree, matching
   working bytes, historical source digest and required ancestry.

Count runs retain 600 s, eight workers and their recorded seeds. Sampling
retains 300 s and 20 requested optima. Probes retain 1800 s. Completed count,
sampling and probe units are read-only; a timeout is a completed measurement.
Gate tests may create isolated correctness fixtures but never rerun those units.

Atomic units record an input/source fingerprint, config, outputs and SHA-256
digests. Interrupted work resumes at unit boundaries. Deterministic fields and
scores must be byte-identical; multiworker search is compared by status,
bounds and exact witnesses, without claiming deterministic search bytes.
New text outputs use UTF-8 and LF with repository-relative paths and no
personal identifiers. New measurements are appended in separate units.

The public cleanup preserves stored hashes in all historical evidence. Private
working documents are omitted; old provenance paths are redacted rather than
retargeted under old hashes. Approved reporting substitutions can make an old
hash unavailable as a check on public bytes. The public gate records each
blocked check separately, executes remaining assertions and makes no full-PASS
claim while checks are blocked. [Provenance](../README.md#provenance) and the
public gate report distinguish these effects from numerical failures.

## 8. Validation leaves evidence unchanged

Tests and gates never write tracked files. Test fixtures and T37 reports use
a short unique directory below the system temporary root, with short per-test
names independent of clone depth and a checked path budget of 200 characters.
Gate reports use ignored results directories. Paths in T37 reports are relative
to the repository; a `<SCRATCH>` prefix identifies temporary output on a
different Windows drive. The full-suite guard rejects tracked-file write access in the
test process, then checks Git status and all tracked hashes after every test
and after the full suite. The gate has the same guard and checks the suite's
guard report. A tracked-file change or newly created unignored file fails
validation. Completed scientific units remain read-only.

After a successful public gate, publishing its scratch report is a separate,
explicit evidence-generation action:

```sh
python scripts/record-gate-evidence.py results/stage1-gate-v1.8.4/<run>/gate.json
```

This validates the current committed tree, all passing unblocked checks and
the 17 approved privacy blockers before writing `docs/stage1-gate-public.json`.
Historical evidence hashes are preserved.
