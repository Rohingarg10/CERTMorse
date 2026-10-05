# Certificate semantics: v1.8 amended through v1.8.3

Stage 1 gate: **PASS**. [Gate report](stage1-gate.json) and
[measurements](STAGE1.md) delimit the evidence. No Stage 2 experiment was run.

## Integer-model certificate

The model maximizes incidence matches; each cell appears in at most one pair.
Matched cofaces have value at most their partner face; unmatched incidences
increase by at least one. Integer potentials lie in the original cell band.
Thus no closed V-path exists. Every accepted matching is independently checked
with exact integer Bellman–Ford and the discrete-Morse validator.
For a CP-SAT upper bound B on matches, kappa_lb=6m²−2floor(B), including at
timeout. Only OPTIMAL establishes kappa*. HiGHS bounds remain numerical
benchmarks. This relies on CP-SAT's integer reasoning and reported bound.
Formulation B's relaxation bound remains valid before its matching is accepted;
both V-cycles and signed band-infeasibility cycles must be separated.

## Region bound and valid rows: proof

For vertex a, C(a) is its component in {v:lo_v<=hi_a} on the six-neighbour
graph. Every boundary vertex w has lo_w>hi_a. The smallest-valued vertex v*
inside C(a) has x_v*<=x_a<=hi_a. If v* were matched to an edge, that edge's
other vertex would have strictly smaller value (the other incidence is
unmatched). Such a vertex exists neither inside C(a), by minimality, nor on
its boundary, by the bound. Hence C(a) contains a critical vertex.

D(b) is triangle b's component in {t:hi_t>=lo_b} in the edge-sharing dual
graph. A matched triangle t paired to edge e has an unmatched neighbouring
triangle t' across e, with x_t'>x_e>=x_t. The largest-valued triangle in D(b)
has value at least x_b>=lo_b; every boundary triangle has value below lo_b.
It therefore cannot be matched and D(b) contains a critical triangle.

Threshold components are laminar: when two overlap, the lower-threshold
component is contained in the higher-threshold component (reverse thresholds
for maxima). Inclusion-minimal members are consequently pairwise disjoint.
Each requires its own critical cell. With k_min and k_max minimal regions,
c0>=k_min and c2>=k_max. Since c0−c1+c2=0 on the torus,
kappa=2(c0+c2)>=2(k_min+k_max)=LB_region.

Region rows encode exactly one or more critical cells per disjoint minimal
region. Morse rows c0>=1,c1>=2,c2>=1 hold for the torus. Substitution of the
matching expressions into Euler cancels every y term and leaves
|V|−|E|+|T|=m²−3m²+2m²=0; the Euler row is identically valid even in the
relaxation. Adding these rows removes no feasible integer matching. Summing
the region rows and Euler gives the same LB_region in the relaxation.
T33 tests preservation for all 120 bands and three methods.

The certified count is max(CP-SAT kappa_lb,LB_region). This applies first to
the integer model; the following coverage/transfer hypotheses connect it to
the true field. LB_mand and persistence counts remain cross-checks.
Together the two bounds give kappa_cert<=kappa*<=kappa_true under those hypotheses.

## Transfer theorem and complete proof


Assume the true vertex field F lies in the reported band. Choose S as specified
and widen narrow intervals if the scale cap binds. Add 14/S outward on each side
before rounding inward. Suppose every adjacent vertex pair has separation at
least 14/S. Let G be the lower-star gradient of F, with the fixed vertex-index
tie rule. Then G is realizable in the integer model.

To prove this, write `a_v = round(S*F(v))`. Each lower rounded bound is at most
`a_v-13`, and each upper rounded bound is at least `a_v+13`. Indeed the outward
margin is 14 and rounding F changes it by at most half a unit; ceil/floor can
consume less than one additional unit. Because endpoints are integers, at least
13 units remain on both sides. Widening at the scale cap cannot weaken this fact.

Assign each cell to its largest vertex in the lower-star order. A torus vertex
has six incident edges and six incident triangles, so its star contains at most
13 cells including itself. On each star, direct matched incidences from the
coface to the face, and unmatched incidences from the face to the coface. This
is the reverse of the acyclic V-path digraph. A topological ordering therefore
gives distinct integer ranks `o(c)` from 0 to at most 12, increasing along every
directed edge. Set `x_c = a_v + o(c)` for cells owned by v. For incidences inside
one star, these ranks give the required matched nonincrease and unmatched
strict increase. Allowing equality on matched pairs only enlarges feasibility.

For an incidence between different stars, let the face be owned by w and the
coface by v. Both vertices belong to the coface simplex and are adjacent. Since
the face is a subset, `F(v) > F(w)`; the separation assumption rules out ties.
The rounded centers differ by at least 13 integer units. Thus
`x_face <= a_w+12 < a_v <= x_coface`, exactly the unmatched strict inequality.
Lower-star matching never matches across stars.

Finally, for any vertex w of a cell owned by v, its integer lower bound is at
most `a_w-13 <= a_v-13`. The maximum of these lower bounds is therefore below
`x_c`. The cell's upper bound, a maximum over its vertices, is at least v's
upper bound `a_v+13`, above every permitted offset. Every cell lies inside its
cell band. This constructs a feasible integer realization of G, proving
`kappa_lb <= kappa_star <= kappa_true` for CP-SAT.


The separation condition is sufficient, not necessary. Simulation records
coverage and direct exact transfer separately, and claims transfer only when
both hold. Ties are counted with |delta F|<1e-12. kappa_true is reported only
without adjacent ties, with the six-neighbour extrema identity; otherwise
kappa_zero is the OPTIMAL fixed-S0=10^6, half-width 500/S0 diagnostic.

## Symmetry, grid and scope

Beta has period pi for all channels and pi/2 for a,b,d,d0,e. Amplitude damping
c breaks pi/2, established by the preserved T29 failure. Its domain is
[0,pi); the others use [0,pi/2). Gamma always has period 2pi. Actual gamma
shift or shift/reflection symmetry is measured at 100 random points, tolerance
1e-12, for each instance/channel; ideal YAML values are reference data only.
Counts use the full applicable torus, with per-copy counts only if divisible.
Conjugation holds continuously for a,b,c and is tested off grid.
Quarter-offset conversions use grid_point/grid_coords, including VTK and
independent references. Synthetic tests retain the original beta-pi grid.

## Basin predictions and resolution

For each matching, basin depth is the minimum observed field value in the
basin, independent of arbitrary witness values. P counts basin areas whose
depth is within tau=0.02W of the smallest depth. P_possible counts basins with
minimum reported lower endpoint <= minimum reported upper endpoint +tau.
The observed depth field G must satisfy lower<=G<=upper at every vertex.
For a basin counted by P, min_B lower<=min_B G<=min G+tau<=min upper+tau:
evaluate G at a vertex attaining min upper for the final inequality.
Therefore P<=P_possible. Both use the reported unscaled band before margins.
The preserved old T32 failure demonstrates why the same tolerance is needed.

The certificate is a grid count statement; it certifies neither basin area nor
continuum minima. The simulation-only resolution test refines basin minima by
Nelder–Mead and compares global classifications. W8a m=16 fails and is excluded
from basin conclusions. RQ2-informative means P0_grid<=0.95 and resolution
adequate. P differences and multiplicity ranges never determine fallback.
Sampling starts only from OPTIMAL; medians are procedural and ranges observed
unless enumeration is exhausted.

## Statistical and persistence contracts

Hoeffding uses independent bounded shot outcomes and Bonferroni over all grid
vertices. Gaussian modes are approximations. The paired 2000-seed study is
recorded in STAGE1.md. The retained adaptive contract covers vertices and every
predeclared deterministic sample size, including data-dependent stopping;
no adaptive Stage 2 experiment is undertaken here.
Persistence uses the closure filtration phi(c)=min over cofaces x(rho),
coefficients Z/2, and top-dimensional persistence, retaining essential
dimensions 0,1,1,2. Both bottleneck sides use that filtration and their scale.
TTK essential endpoints are decoded with IsFinite.

## What the MIP adds beyond the region bound

| Dataset | kappa*=LB_region / optimal | LB_region=LB_mand / 20 |
| --- | --- | --- |
| R8a-hoeffding | 18/18 | 20/20 |
| E8a-hoeffding | 20/20 | 20/20 |
| W8a-hoeffding | 15/15 | 16/20 |
| R8a-oracle | 20/20 | 20/20 |

Random-band T31 equality is 26/50; the count solve can add information beyond the region bound.

## Equivalent numerical representation and TTK starts


HiGHS uses binary matchings with continuous cell potentials. For fixed y the
difference-constraint matrix is a network matrix; integer bounds imply an
integer realization whenever a real one exists. Internal endpoint compression
caps every gap between sorted distinct integer endpoints at |K|. A simple path
has at most |K|-1 strict steps, so every endpoint difference comparison needed
for feasibility is preserved. Directed negative cycles remain infeasible
independently of the coordinate map. Thus the matching projection is unchanged.
Per-incidence big-M constants follow from those compressed bounds. Neither the
numerical potentials nor compressed coordinates are used for persistence or
the returned certificate: exact witnesses always use the original model band.

TTK simplification preserves essential classes and exports its scalar ordering.
The lower-star candidate uses lexicographic (Scalar,Scalar_Order) ranks and is
accepted only after witness verification in the original band. UB_pers is
justified only if that candidate also has count <= UB_pers. A larger feasible
count would still leave UB_pers as a reference. The substantive API and claim
changes are specified in ../PRIVATE_DOCUMENT_06.
