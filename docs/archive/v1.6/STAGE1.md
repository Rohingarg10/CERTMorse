# Stage 1 evidence for specification v1.6

Status: **OPEN — no v0.1 release; no Stage 2 implementation.**

The code and commands are documented in README.md. Reservations and changes
are recorded in PRIVATE_DOCUMENT_14; mathematical claims are in CERTIFICATE.md.

## Recorded local checks

The combined local suite passed **119 tests in 185.08 s**, including TTK and
TimesFM. The earlier core suite passed 114 tests in 147.77 s, including the full noisy-landscape
gate. The added HiGHS regression passed separately. Its raw report is
core-tests.xml; execution output is results/stage1/core-tests.log. External
checks passed separately: TTK count/persistence agreement on 20 smooth m=16
fields and the near-zero mandatory-minimum test (51.80 s); all three reference
adapter smoke checks (5.52 s); TimesFM CPU T17 and throughput (tsfm-smoke.json).

| Tests | Evidence and scope |
|---|---|
| T1 | Same canonical run and its dedicated .rerun NPZ agree to 1e-12; completion/resume tested |
| T2, T2b | All 12 ideal m=16 fields checked against closed form or independent NumPy |
| T3 | 200 seeds, 186 covered, z=3.7250035156206223; independent formula check; coverage.json |
| T4 | Counts and incidences for m=3,4,8,16 |
| T5, T15, T22 | Known sinusoid counts and basin areas; ties and zero-valued fields; basin partition |
| T6, T7 | 20 smooth-field TTK critical-count comparisons; mandatory minima near zero width |
| T8, T23(ii) | Small smoke checks pass; full randomized sweep finds HiGHS disagreements; gate FAILS |
| T9–T11 | R8a 20-band count bounds, Morse identities, exact matching validation and transfer measurements |
| T14 | Hypothesis: 200 m=4 matchings, witness iff fixed-y A feasible |
| T16 | Perfect torus field: four essential classes and n(delta)=4 |
| T17 | CPU wrapper shapes, exact/shot covariates, repeated-batch determinism, invalid-shape rejection |
| T19 | Ideal and noisy channels a–c on all 12 m=16 grids; involution and 1e-12 symmetry |
| T20 | 50 m=4 bands, 200 random candidates per band; direct and actual lazy cuts checked against accepted candidates and A optima |
| T21 | Config canonicalization/defaults and complete/incomplete resume behavior |
| T23(i), T26 | m=16 narrow-band optima 4 and 8; explicit six-cell collapse accepted by loose bounds, rejected by cell band |
| T24 | 20 smooth-field TTK/GUDHI comparisons; four essential classes; certified persistence count <= optimum |
| T25 | d,d0,e periodicity at directly evaluated off-grid points on all 12 instances |
| T27 | 100 off-grid translation checks on every instance; weighted controls fail identity as required |
| T28 | 100 random matchings at m=3,4; every feasible vertex range checked with independent LPs; infeasibility checked too |

The successful unit checks do not erase the failed full cross-method gate.
The agreement runner preserves status, bound, matching, log and MPS evidence
under results/stage1-agreement*; aggregate rows are in agreement.json.

The full sweep completed all 120 bands: 50 each at m=3 and m=4, and 20 at m=8.
CP-SAT A and B agree on all 118 cases where both are OPTIMAL. B reaches
CUT_LIMIT on m=4 seeds 2305 and 2342; its incumbent is not called optimal.
At m=8, CP-SAT A/B are OPTIMAL and agree on all 20 bands. HiGHS reports a
different optimum in eight cases: (m,seed) = (3,2300), (3,2326), (4,2325),
(4,2330), (4,2334), (8,2308), (8,2309), (8,2319). These disagreements block
the required backend agreement despite the unit-suite pass.

## Required R8a measurements

stage1-r8a.csv contains 20 seeded m=16 oracle bands at N=1000. Every solve
proved kappa*=32. LB_mand, LB_pers and UB_pers are 32 in every row. No reference
bound violation occurred on these bands. Direct transfer succeeded in all 20,
despite sep_min=0; coverage was true in 19 of them. The true rounded-field
gradient has 34 critical cells. These are discrete grid measurements.

Ten bands each supplied 20 distinct optimal vertex-edge matchings, with
sampling_status=complete. Their observed P spread ranges from 0.44921875 to
0.6875. This is material. RQ2 must treat the predictions as a set; procedural
medians remain descriptive rather than a certified unique success probability.
The ranges are observed, not exhaustive. See figures/basin-spread.png.

Warm-start simplification was audited separately after these solves. All
candidates passed the cell-band witness, but their critical counts were larger
than the persistence reference. The audit is warm-start-audit.csv; it is not
retroactively reported as solver-start usage.

![Exact field, sampled field, and one optimum's predicted basins](figures/r8a-stage1.png)

## Gate disposition

1. Test gate: open because the full T8/T23 cross-method agreement is not met.
2. Known answers and collapse control: pass; randomized cross-method part fails.
3. m=8 full cross-method gate: A/B on CP-SAT agree in all 20 cases;
   backend agreement fails in three cases and requires HiGHS investigation.
4. Twenty-band mandatory/optimum/persistence reference comparison: measured;
   holds on all 20 bands, with warm-start/reference caveat above.
5. Ten-band optimum multiplicity measurement: complete; material spread found.
6. Persistence contract: passes the 20-field check.
7. Certificate semantics and full conditional transfer proof: written.

No gate is waived. No version tag is created until all required checks pass.
