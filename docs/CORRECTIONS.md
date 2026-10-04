# Stage 1 correction findings

Specification: [public method](METHOD.md). Original results and
documents remain available in the v1.6 archive. Gate status is recorded by
[stage1-gate.json](stage1-gate.json), rather than inferred from small smoke tests.

## Solver correctness

The historical sweep found eight HiGHS count disagreements and two formulation
B cut limits. CP-SAT optima satisfy the exported MPS rows in exact integer
arithmetic. Direct-model and MPS runs reproduce the same HiGHS failures.
Presolve/hint changes and local big-M constants alone do not fix every case.
Changing from HiGHS 1.15.1 to 1.12.0 alone also leaves counterexamples.

The qualified representation uses continuous cell potentials with binary
matching variables, exact endpoint compression and per-incidence big-M
constants. Network-matrix integrality proves that a feasible fixed matching
still has integer potentials. Endpoint compression preserves every comparison
between an endpoint difference and a possible strict-path length. The original
matching problem therefore stays unchanged. Exact Bellman–Ford reconstructs
and checks every accepted solution against the original model band.

All 18 historical regression cases pass with/without hints. The first corrected
full 120-band sweep gave equal OPTIMAL counts from all three methods. This is
evidence for the qualified version and settings, not a proof about every future
numerical solve. HiGHS bounds remain numerical; they are never count certificates.

Formulation B now separates multiple conflicts per incumbent and deduplicates
cuts. Band conflicts come from subgraphs of the original difference graph, so
each retained signed cut excludes an actual infeasibility pattern. It retains
the strongest relaxation bound. The final sweep's maximum was 88 separation
rounds, within the unchanged 200-round cap. Round count and cuts added are
reported separately. T20 checks that the actual generated cuts preserve feasible
matchings and the independently solved A optimum.

## TTK ordering and warm starts

Simplification creates scalar plateaus whose `Scalar_Order` carries the intended
tie order. Dropping it made ProcessLowerStars use vertex-index ties and introduce
additional critical cells. Both arrays are now retained. A unique rank surrogate
realizes their lexicographic order for gradient extraction, while an exact
witness checks feasibility in the original cell band. This changes neither the
public scalar tie rule nor the physical confidence band.

Essential persistence classes are explicitly retained in simplification
constraints. All 20 audited candidates now have 32 critical cells and exact
witnesses. Scalar-only reconstruction on the same outputs gives 36–44. Their
count now also meets UB_pers=32, so the upper reference is justified for those
candidates. Feasibility alone would not establish that inequality.

The new R8a driver runs this simplification before solving, compares candidates
with the midpoint matching, and records the start actually used. Original runs
are still described as midpoint-start runs; a later audit is not retroactive use.

## Confidence bands and transfer

Original Gaussian calibration remains 186/200, with its original formula and
threshold retained. A paired independent study on seeds 10000–11999 found
1898/2000 Gaussian bands covering all vertices: 94.9%, Wilson 95% interval
93.85–95.78%. It observed 105 vertex failures across 83 vertices, including
vertices with nonzero skewness. Those diagnostics do not isolate a single cause
of undercoverage.

Hoeffding covered 2000/2000 in the same study. The finite-sample guarantee comes
from bounded independent shots and the union bound, rather than this measurement.
Its last-seed mean half-width was approximately 0.815 versus 0.218 for Gaussian
bands. The wider interval is the cost of the guaranteed construction. Hoeffding
is the operational default; legacy oracle measurements remain approximate.

Coverage, direct matching transfer and adjacent separation are distinct flags.
The 14/S margin and conditional transfer proof remain unchanged. R8a has zero
adjacent separation, so its matching is checked directly. A transfer claim is
made only for a covered band whose true matching passes that check.

The old driver rounded the shot-free field before computing `kappa_true`. The
new driver reports the computed shot-free field's gradient count separately from
the rounded diagnostic: 42 versus 34 for this saved numerical field. Floating
near-ties and explicit rounding can alter the vertex order. Neither count is a
certificate about the continuum; the matching used in a transfer check is stated.

## Basin predictions and budgets

Count-optimal matchings have materially different basins. Warm starts can change
the first optimum found, so P_first is also procedure dependent. RQ2 now studies
the observed set of predictions, with the sampled range, procedural median,
sample count and sampling status. A requested sample of 20 is not exhaustive
enumeration or uniform sampling over optima. The gate recomputes the saved basin
statistics and checks matching distinctness and exact feasibility.

Timeouts retain the incumbent, count bound, gap, nodes and actual budget, with
no `kappa_opt`. The old m=32 result is a 16–36 count sandwich; its omitted
incumbent is recoverable from objective 3054 in the raw log. The repeated
benchmark driver now retains all these fields and supports explicit pilot caps.
An isolated timing cannot establish full Stage 2 hours. Larger-grid planning
uses capped pilots and records unresolved gaps as outcomes.

The additional guaranteed-band R8a pilot at m=16/N=1000 hit its 600-second
cap: FEASIBLE, count bound 4 and verified incumbent 20. Its TTK simplification
candidate was infeasible in the cell band and was correctly rejected; the solve
used the midpoint fallback. UB_pers=18 therefore remains an unjustified reference.
Coverage and direct transfer both held. Wider guaranteed bands increase the
matching search space, and the successful oracle fixture timings cannot predict
their solve times. This pilot is separate from the required oracle-band gate.
See stage1-r8a-v1.7-hoeffding.csv.
