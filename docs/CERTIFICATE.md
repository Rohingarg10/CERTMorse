# Certificate semantics for specification v1.7

This is the Stage 1 implementation's mathematical contract. The Stage 1 verification gate
passes the requirements recorded in STAGE1.md and stage1-gate.json.

## What the integer solve establishes

The model maximizes the number of matched incidence pairs on the specified
triangulation of the sampled torus. Each cell is in at most one pair. Matched
cofaces have value at most their partner face; every unmatched incidence has
coface value at least face value plus one. All values are integers inside the
model's cell band. Consequently a closed V-path is impossible: every matched
step is nonincreasing and the following unmatched step decreases by at least
one. Exact Bellman–Ford checks the returned matching independently of the
backend's returned values.

For a solver upper bound B on the maximum number of matches, the lower bound
on the critical-cell count is `6*m*m - 2*floor(B)`. This remains a bound when the
solve times out. Only an OPTIMAL solve establishes κ*. Incumbents, proven count
bounds and optima are separate fields. Only CP-SAT count bounds are labelled
certificates. This relies on the correctness of CP-SAT's integer reasoning and
reported bound; cross-solver agreement is evidence, not a proof of its software.
HiGHS bounds are numerical benchmark results, even after exact witness checking.

Formulation B begins with a relaxation. A directed V-cycle excludes its matched
pairs together. A band-infeasibility cycle instead excludes the full signed
choice of matched and unmatched participating pairs. Retaining that choice
would retain the same negative cycle. Dropping the unmatched terms would not be
sound. Until a B incumbent passes both checks, its relaxation bound can be used
but its matching cannot be accepted as a feasible incumbent.

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

The condition is sufficient and is not required by the exact feasibility check.
R8a has an exactly constant γ=0 column, so its adjacent minimum separation is
zero. Simulation checks `transfer_ok` directly against each covered band's
true computed-field matching, and reports its separation. Its rounded-field
count is a separate diagnostic. Deployment cannot
check separation against an unknown true field. Claims are accordingly stated
as proved under the condition, verified per simulated instance, or assumed.

## Statistical and persistence contracts

Hoeffding bands use bounded independent shot outcomes. Bonferroni covers all
grid vertices. Adaptive allocation selects among the predeclared deterministic
sample sizes `n_0=200`, `n_(k+1)=n_k+max(200,ceil(n_k/2))`. Dividing alpha by
`r_max+1` covers every vertex at every possible sample size by a union bound,
including data-dependent selection and stopping. A union bound over round
numbers alone would not justify data-dependent sample sizes. Each arm must use
an independent stream and fresh shots. The uniform arm's sizes are fixed
conditional on the independent adaptive arm's observations. Oracle and empirical
Gaussian bands are approximations, with a variance safeguard for empirical
zero variance and small sample size. Formula verification does not establish
coverage. Hoeffding is the operational default; Gaussian modes remain
approximate. The original 200-seed measurement and the fresh 2,000-seed paired
study are recorded separately in coverage.json and coverage-study-v1.7.json.

Persistence uses the closure filtration `phi(c)=min{x(rho): rho contains c}` on
the original torus. Faces enter no later than cofaces. GUDHI uses coefficients
in Z/2 and retains top-dimensional persistence, giving essential dimensions
0,1,1,2. Both sides of a bottleneck comparison use this same function and divide
integer values by S. TTK cross-checks the vertex lower-star side only; its
display endpoints for essential classes are decoded using the discovered
`IsFinite` flag, not their finite displayed death coordinates.

## Limits of the result

The certificate concerns counts on the sampled grid. It does not certify the
continuum between vertices, critical-point locations, or basin predictions.
Reference mandatory and persistence bounds concern related piecewise-linear
classes and are not substituted for solver bounds. Their violations are findings.
An optimum can have several matchings and realizations. Basin scores use the
observed mean at critical vertices, avoiding dependence on arbitrary witness
values. Sampling requires an OPTIMAL initial solve. Unless enumeration is
exhausted, the reported basin range is an observed range and the median is
specific to the sampling procedure, rather than a uniform measure over optima.

## Equivalent numerical representation

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
