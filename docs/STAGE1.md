# Stage 1 evidence for v1.8, amended through v1.8.3

**Gate status: PASS.** Evaluated by `scripts/stage1-gate.py`; the executable
[gate report](stage1-gate.json) contains commands, exit codes, source digest,
logs and independent artifact checks. Branch: `v1.8`. No Stage 2 module or experiment was started.
The source digest is `ac3e847b9f8846eb8d599ea96ce128ea49c42ff43bb73da3e2a50d972f41823f`.

The gate recorded 326 passing tests and
0 skipped tests.
Failed requirements: [].

## Independent review and preserved failures

Before implementation, every requested v1.8 §3 finding reproduced:
all 200 archived optima gave depth P=1 (old critical-vertex scoring reached
0.27734375); all 12 ideal fields passed beta pi/2 and their listed gamma
symmetries; R8a had 112 old-grid adjacent ties and the quarter grid had zero
ties on all twelve ideal instances at m=16 and 32; all 20 archived R8a oracle
bands gave LB_region=32 (eight minimum and eight maximum regions).
[Independent reproduction](review-reproduction-v1.8.json).
The explicit symmetry lists contain eight symmetric and four nonsymmetric
instances; v1.8's prose count of nine and three is inconsistent with those lists.

The v1.7 archive contains 6,872 byte-preserved files and its SHA-256 manifest.
[Archive](archive/v1.7/README.md). The gate checks the archive hashes and original
result-file hashes. New measurements use separate v1.8.3 result directories.

The original T29 run stopped with **2 passed, 1 failed**: R8a amplitude damping
breaks beta pi/2 with error **0.014559172029865675** (point seed 29, circuit seed 7).
[Failing T29 XML](v1.8-amendment-preflight.xml),
[original gate](v1.8-preflight-gate.json).
V1.8.1 replaces that assertion: beta pi for every channel, pi/2 for all except
amplitude damping, whose R8a half-period failure is a required negative control.
Measured per-channel gamma metadata accompanies the saved fields.

The original T32 run stopped with **1 failed**: on the proven kappa=16 narrow-band
R8a optimum, P=1 but the old P_possible=0.5234375.
[Counterexample](t32-counterexample-v1.8.1.json),
[failing XML](v1.8.1-basin-preflight.xml),
[preserved gate](v1.8.1-preflight-gate.json).
V1.8.2 adds the same 0.02W tolerance to P_possible; the preserved counterexample
now gives P=P_possible=1. The old definition remains a named test control.
The scorer asserts that the depth field lies in the reported band.

The first full-gate attempt was interrupted by laptop standby and hibernation.
E8a seed 9 exhausted its elapsed presolve budget with no initialized objective
bound; the numerical guard rejected that response. The failed gate and all
affected evidence were archived before recovery. R8a seed 4 and E8a seeds 5-9
were replayed because their execution intervals overlapped recorded standby;
all other completed runs, including the two R8a timeouts, were retained.
Recovery uses the original seeds and 600 s count / 300 s sampling caps and
a temporary Windows wake request, released when the launcher finished.
No scientific rule or threshold changed.
[public method](METHOD.md), [recovery manifest](stage1-sleep-recovery.json).

## Amendment checks

Synthetic fields retain the v1.6 beta-pi grid and known answers. QAOA uses
the single quarter-offset `grid_point`/`grid_coords` conversion, tested by T35.
Strict extrema use the six triangulation neighbours. Fixed-scale kappa_zero
uses S0=10^6 and half-width 500/S0 with the unchanged 14-unit margin.

T31 solved 50 random m=4 bands to OPTIMAL, verified the
disjoint regions and critical cells, and found LB_region=kappa* on
26/50 (52%).
T33 compares the same 120 bands, three methods, with and without rows (720 solves).
The gate independently rechecks the saved witnesses, bounds and counts.

## T34: archived bands, measured before the full gate

Both arms use identical archived integer bands, hints, seeds, eight threads
and the original caps (600 s Hoeffding; 60 s m=32). Improvement is not asserted.
[T34 measurements](T34-v1.8.3.json).

| Band | Rows | Status | Count bound | Incumbent | Optimum | Seconds |
| --- | --- | --- | --- | --- | --- | --- |
| hoeffding | no-rows | FEASIBLE | 4 | 18 | None | 600.27 |
| hoeffding | rows | FEASIBLE | 14 | 20 | None | 600.27 |
| m32-0 | no-rows | FEASIBLE | 4 | 32 | None | 60.93 |
| m32-0 | rows | OPTIMAL | 32 | 32 | 32 | 29.76 |
| m32-1 | no-rows | FEASIBLE | 4 | 32 | None | 60.96 |
| m32-1 | rows | OPTIMAL | 32 | 32 | 32 | 34.29 |
| m32-2 | no-rows | FEASIBLE | 4 | 32 | None | 60.91 |
| m32-2 | rows | OPTIMAL | 32 | 32 | 32 | 28.52 |

For the archived Hoeffding pilot the count bound changed from 4
to 14, the incumbent from 18 to
20, and status from FEASIBLE to FEASIBLE.
LB_region in the row arm is 14. The archived v1.7 run itself
was FEASIBLE at 600 s with count bound 4 and incumbent 20. The paired current
no-row arm is the appropriate control for isolating the rows.

## Full-gate measurements

| Dataset | Optimal | Timeouts | Optimum=region | Region=mandatory | Sampled bands | Optima | Observed P spread |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R8a-hoeffding | 18 | 2 | 18/18 | 20/20 | 10 | 18 | [0.0, 0.0] |
| E8a-hoeffding | 20 | 0 | 20/20 | 20/20 | 10 | 87 | [0.0, 0.0] |
| W8a-hoeffding | 15 | 5 | 15/15 | 16/20 | 10 | 32 | [0.0, 0.89453125] |
| R8a-oracle | 20 | 0 | 20/20 | 20/20 | 0 | 0 | None |

E8a: 0/10 sampled bands show nonzero P spread; range [0.0, 0.0]. Resolution passes; this is an eligible basin measurement.

W8a: 1/10 sampled bands show nonzero P spread; range [0.0, 0.89453125]. Resolution fails at m=16; these raw solver measurements are excluded from basin-prediction conclusions.

R8a-hoeffding: sampled count range [1, 5], statuses {'time_capped': 10}.

E8a-hoeffding: sampled count range [3, 15], statuses {'time_capped': 10}.

W8a-hoeffding: sampled count range [2, 4], statuses {'time_capped': 10}.

Sampling uses the fixed count, random secondary vertex-edge weights, signed
no-good cuts and first-feasible solves; cap 20 optima including the first,
300 s per band. Ranges are observed and medians procedural, not uniform samples.

The ten sampling bands are the first ten OPTIMAL bands in seed order. If a
primary sampling slot times out in count optimization, supplemental sampling
uses an already proven subsequent band among the same twenty; its separate
configuration and logs are linked by `multiplicity_run_path`. No primary count
solve is repeated, and no cap or threshold is changed.

Independent sampling verification passed for all 30 selected bands,
including the six supplemental bands: unchanged source and driver hashes,
seed selection, fixed caps, primary/sidecar arrays and every saved basin
score were checked. [Verification](multiplicity-verification-v1.8.3.json).

## Resolution check

| Instance | m | Adequate | Worst depth error | P0 grid | P0 continuous | Informative |
| --- | --- | --- | --- | --- | --- | --- |
| E8a | 16 | True | 0.075776 | 0.507812 | 0.507812 | True |
| E8a | 24 | True | 0.073263 | 0.500000 | 0.500000 | True |
| E8a | 32 | True | 0.022933 | 0.484375 | 0.484375 | True |
| E8a | 48 | True | 0.012127 | 0.480469 | 0.480469 | True |
| E8b | 16 | True | 0.209322 | 0.453125 | 0.453125 | True |
| E8b | 24 | True | 0.118104 | 0.449653 | 0.449653 | True |
| E8b | 32 | True | 0.058318 | 0.440430 | 0.440430 | True |
| E8b | 48 | True | 0.014924 | 0.433160 | 0.433160 | True |
| W8a | 16 | False | 1.591198 | 0.093750 | 0.214844 | False |
| W8a | 24 | False | 0.657528 | 0.105903 | 0.197917 | False |
| W8a | 32 | True | 0.207514 | 0.191406 | 0.191406 | True |
| W8a | 48 | True | 0.158690 | 0.187934 | 0.187934 | True |
| W8b | 16 | False | 1.889753 | 0.101562 | 0.242188 | False |
| W8b | 24 | True | 0.681614 | 0.168403 | 0.168403 | True |
| W8b | 32 | False | 0.771466 | 0.081055 | 0.157227 | False |
| W8b | 48 | True | 0.303072 | 0.152344 | 0.152344 | True |
| R8a | 16 | True | 0.135661 | 1.000000 | 1.000000 | False |
| R8a | 24 | True | 0.059195 | 1.000000 | 1.000000 | False |
| R8a | 32 | True | 0.044554 | 1.000000 | 1.000000 | False |
| R8a | 48 | True | 0.023048 | 1.000000 | 1.000000 | False |

[Resolution artifacts](resolution-v1.8.3.json). Nelder–Mead uses xatol=1e-9,
fatol=1e-12 and stops when its iterate leaves the starting basin's half-open
nearest-vertex grid cells (the equal vertex-area convention of D11).
The measured smallest passing sizes are {'E8a': 16, 'E8b': 16, 'W8a': 32, 'W8b': 24, 'R8a': 16}.
These follow the amendment's classification rule; its forecast of m=32 for
E8a/E8b/R8a and m=48 for W8b is not the measured minimum. Adequacy is not
monotonic: W8b passes m=24 but fails m=32.
The p=2 fallback is False; informative E8a/E8b pairs are
available. No spread or agreement measurement is used as a switching criterion.

## Paired coverage

| Band | Covered / 2000 | Coverage | Wilson 95% | Guarantee |
| --- | --- | --- | --- | --- |
| oracle | 1896/2000 | 0.948 | [0.9373820458455553, 0.956900279790442] | False |
| hoeffding | 2000/2000 | 1.0 | [0.9980829527187469, 0.9999999999999998] | True |

Seeds 10000–11999, paired shots on the new R8a grid. Gaussian coverage is
measured and approximate; Hoeffding has the bounded-shot union-bound guarantee.
[Coverage study](coverage-study-v1.8.3.json).
