# Stage 1 evidence for v1.8, amended through v1.8.4

The current [v1.8.4 gate report](stage1-gate-v1.8.4.json) records all six
completion items. The [corrections below](#v184-corrections-and-completion)
give the authoritative re-scored tables and limits. No Stage 2 work was started.

**Historical v1.8.3 gate status: PASS against an incomplete measurement list.** The executable
[gate report](stage1-gate.json) contains commands, exit codes, source digest,
logs and independent artifact checks. Branch: `v1.8`. No Stage 2 module or experiment was started.
The historical source digest, pinned by `stage1-v1.8.3`, is
`ac3e847b9f8846eb8d599ea96ce128ea49c42ff43bb73da3e2a50d972f41823f`.
The current committed-source digest is recomputed in the v1.8.4 gate report.

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

## Historical v1.8.3 measurements

Here and throughout this report, *P* estimates `P0_res`, the true success
probability at the band's resolution, and is never a certificate. When
sub-resolution minima exist it does not estimate *P*₀. For E8a, zero certified
traps and resolution 2.717949 accompany *P* = 1; for W8a Hoeffding, zero
certified traps and resolution 5.979487 accompany the saved *P* values.

| Dataset | Optimal | Timeouts | Optimum=region | Region=mandatory | Sampled bands | Optima | Observed P spread |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R8a-hoeffding | 18 | 2 | 18/18 | 20/20 | 10 | 18 | [0.0, 0.0] |
| E8a-hoeffding | 20 | 0 | 20/20 | 20/20 | 10 | 87 | [0.0, 0.0] |
| W8a-hoeffding | 15 | 5 | 15/15 | 16/20 | 10 | 32 | [0.0, 0.89453125] |
| R8a-oracle | 20 | 0 | 20/20 | 20/20 | 0 | 0 | None |

E8a: 0/10 sampled bands show nonzero P spread; range [0.0, 0.0]. The grid
resolution check passes, but *P* = `P0_res` = 1 differs from *P*₀ = 0.5078125;
κ* = 8 is below κ_true = 12. There are zero certified traps at resolution
2.717949. The explanation and oracle comparison appear below.

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
The historical smallest passing sizes were {'E8a': 16, 'E8b': 16, 'W8a': 32, 'W8b': 24, 'R8a': 16}.
These follow the amendment's classification rule; its forecast of m=32 for
E8a/E8b/R8a and m=48 for W8b is not the measured minimum. Adequacy is not
monotonic: W8b passes m=24 but fails m=32. The v1.8.4 monotone rule therefore
chooses W8b m=48; the other choices remain E8a 16, E8b 16, W8a 32 and R8a 16.
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

## v1.8.4 corrections and completion

The governing [public method](METHOD.md)
corrects the meaning of *P* and completes the original gate's missing items.
*P* is the success probability of the simplest landscape consistent with the band.
It estimates the true success probability at the band's resolution, `P0_res`;
it is never a certificate. It does not estimate *P*₀ when unresolved minima
remain in the true field. `P_possible` is withdrawn as an ambiguity measure:
it cannot see erased basins. The saved column is `P_possible_simplest`, retained
for continuity with the assertion *P* ≤ `P_possible_simplest`, and used in no conclusion.

### Re-scored Hoeffding and oracle results

All six datasets use *m* = 16, channel (a), *N* = 1000, α = 0.05,
field seed 1003 and band seeds 0–19. Ranges of κ* and *P* here refer only to
proved OPTIMAL bands; trap and resolution ranges cover all twenty bands.
Reported *P* is the procedural median when sampled, otherwise the first-optimum
value; exact `P_first` and sampled ranges remain in the CSVs.
`P0_res` merges minima below the median full reported band width; `resolution`
is twice the maximum full width, the sufficient visibility threshold.
The `trivial` column counts κ* = 4 bands, whose *P* = 1 follows by construction.
Such bands are kept separate from non-trivial RQ2 measurements. Each CSV also
contains `P0_res_guaranteed`, visible-minimum counts and every per-band value.

| Instance / band / exact CSV | OPTIMAL | κ* | κ_true | *P* (reported) | *P*₀ | `P0_res` | `n_traps_cert` | `resolution` | `trivial` (OPTIMAL) | abs(*P* − `P0_res`) | abs(*P* − *P*₀) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [R8a hoeffding](stage1-r8a-hoeffding-rescored-v1.8.4.csv) | 18/20 | 10–12 | 16 | 1 | 1 | 1 | 0 | 3.261539 | 0/18 | 0 | 0 |
| [R8a oracle](stage1-r8a-oracle-completion-rescored-v1.8.4.csv) | 20/20 | 16 | 16 | 1 | 1 | 1 | 0 | 1.108155 | 0/20 | 0 | 0 |
| [E8a hoeffding](stage1-e8a-hoeffding-rescored-v1.8.4.csv) | 20/20 | 8 | 12 | 1 | 0.507812 | 1 | 0 | 2.717949 | 0/20 | 0 | 0.492188 |
| [E8a oracle](stage1-e8a-oracle-completion-rescored-v1.8.4.csv) | 20/20 | 8 | 12 | 1 | 0.507812 | 1 | 0 | 0.972242 | 0/20 | 0 | 0.492188 |
| [W8a hoeffding](stage1-w8a-hoeffding-rescored-v1.8.4.csv) | 15/20 | 4–6 | 48 | 0.414062–1 | 0.09375 | 1 | 0 | 5.979487 | 14/15 | 0–0.585938 | 0.320312–0.90625 |
| [W8a oracle](stage1-w8a-oracle-completion-rescored-v1.8.4.csv) | 10/20 | 14–20 | 48 | 0.054688–0.472656 | 0.09375 | 0.394531 | 2–4 | 2.229444 | 0/10 | 0.039062–0.339844 | 0.039062–0.378906 |

### Persistence recomputed from the saved fields

The table below was recomputed by union-find with the elder rule on all twenty
saved shot-free resolution fields, using the six-neighbour D5 triangulation.
Non-global means value > min *G* + τ_min, with τ_min = 0.02*W*; the essential
minimum has infinite persistence. Exact pairs, births, deaths and field hashes
are in [persistence-v1.8.4.json](persistence-v1.8.4.json).
Finite global-class pairs are included to make the R8a control comparison explicit.

| Instance | *m* | Non-global minima | Their persistence | Their values | −*W*/2 | Finite persistence of global-class minima |
| --- | --- | --- | --- | --- | --- | --- |
| E8a | 16 | 2 | 0.003656–0.015802 | -5.009777–-5.003218 | -5 | 1.559862 |
| E8a | 24 | 3 | 0.000054–0.012105 | -5.009748–-4.999995 | -5 | 1.588635 |
| E8a | 32 | 3 | 0.000024–0.011772 | -5.00944–-4.999999 | -5 | 1.64825 |
| E8a | 48 | 3 | 0.000008–0.010496 | -5.009971–-5 | -5 | 1.665717 |
| E8b | 16 | 4 | 0.07046–0.102905 | -8.598667–-8.575811 | -8.5 | 1.525093 |
| E8b | 24 | 4 | 0.08197–0.103006 | -8.602806–-8.583415 | -8.5 | 0.027162–1.660194 |
| E8b | 32 | 4 | 0.088273–0.104832 | -8.60434–-8.589878 | -8.5 | 1.735634 |
| E8b | 48 | 4 | 0.095773–0.105288 | -8.605187–-8.596592 | -8.5 | 1.790302 |
| W8a | 16 | 11 | 0.009758–2.696415 | -13.917137–-11.256423 | -11 | — |
| W8a | 24 | 12 | 0.028016–3.750113 | -14.850807–-11.398803 | -11 | — |
| W8a | 32 | 10 | 0.334224–1.380315 | -12.626067–-11.380196 | -11 | 4.243662 |
| W8a | 48 | 10 | 0.382927–1.437146 | -12.634413–-11.427327 | -11 | 4.324075 |
| W8b | 16 | 10 | 0.007857–2.840794 | -17.171945–-14.015945 | -14 | — |
| W8b | 24 | 11 | 0.003822–1.054117 | -15.249878–-14.010313 | -14 | 4.226702 |
| W8b | 32 | 16 | 0.000141–4.202705 | -18.290232–-14.012065 | -14 | — |
| W8b | 48 | 18 | 0.000016–1.111769 | -15.311556–-14.009942 | -14 | 4.719324 |
| R8a | 16 | 0 | — | — | -6 | 1.567589–1.686092 |
| R8a | 24 | 0 | — | — | -6 | 1.67548–1.729362 |
| R8a | 32 | 0 | — | — | -6 | 1.701246–1.740998 |
| R8a | 48 | 0 | — | — | -6 | 1.73074–1.754368 |

At E8a *m* = 16, the two non-global minima have persistences 0.003656 and
0.015802 and values −5.003218 and −5.009777, beside the random-cut valley
−*W*/2 = −5. At W8b *m* = 48, eight dimples have persistence
0.000016–0.018359 and values −14.737048 to −14.009942; the other ten
have persistence 0.211971–1.111769. These are saved-field measurements.

### Why counts and basin success differ

A wide band allows nearby low points and their separating saddles to disappear
from a simplest consistent field. Once a basin disappears, measuring success
on that field cannot recover its original area. Persistence measures the height
needed to join a minimum to an older component. The proposition in
[CERTIFICATE.md](CERTIFICATE.md#reported-band-resolution-proposition-v184-22)
guarantees a distinct minimum region above persistence 2*w*; it allows shallower
features to disappear. `P0_res` makes the comparison at the band's resolution.

R8a goes from κ* = 10–12 under Hoeffding to κ* = 16 = κ_true under oracle.
Its finite minima persist for 1.567589–1.686092 (about 1.57–1.69), above the
oracle resolution 1.108155 (1.11) and below the Hoeffding resolution 3.261539
(3.26). This is consistent with the narrower oracle bands retaining those minima.
All minima are global-class, so *P* = *P*₀ = `P0_res` = 1 in both modes.

E8a has κ* = 8 in both modes against κ_true = 12. The four missing cells
are the two sub-resolution dimples and their saddles. Thus *P* = `P0_res` = 1
while *P*₀ = 0.5078125 (0.508): there are zero certified traps and the resolutions
are 2.717949 (Hoeffding) and 0.972242 (oracle). The discrepancy is a limit of
what these bands can resolve, even though the grid resolution check passes.

W8a oracle certifies 2–4 traps per band, proving *P*₀ < 1 under band coverage.
Its first-optimum *P* is 0.054688–0.472656, against `P0_res` = 0.394531 and
*P*₀ = 0.093750, at resolution 2.229444. W8a fails the grid resolution check
at *m* = 16, so no basin-prediction conclusion is drawn in either band mode.
The Hoeffding resolution is 5.979487, with zero certified traps; fourteen
proved bands have κ* = 4 and hence *P* = 1 by construction.

### Original gate gaps and section 6.2 completion

The v1.8.3 PASS used an incomplete measurement list: it included only R8a oracle
counts and omitted all oracle multiplicity sampling. It therefore left 40 oracle
counts and 30 sampling runs required by the original gate unfinished. Its E8a
report also failed to compare *P* = 1 with *P*₀ = 0.508 or κ* < κ_true.
The uncommitted-state gap was closed by the section 8 and subsequent commits,
preserving the original `stage1-v1.8.3` tag and pinned digest separately.

Section 6.2 completed the 40 missing counts: E8a 20/20 OPTIMAL; W8a 10/20
OPTIMAL and 10/20 FEASIBLE at 600 s. The twenty R8a oracle counts were reused.
Thirty oracle sampling runs found 411 optima: R8a 200, E8a 200, W8a 11.
The saved [completion records](oracle-completion-v1.8.4.json) and
[hash manifest](completion-evidence-v1.8.4.json) retain every unit and its settings.

### Sampling selection and limits

| Instance / band | Selected seeds | Optima | Per band | Time-capped | Saved sampled *P* values | `n_traps_cert` | `resolution` | Observed within-band spread | abs(sampled *P* − `P0_res`) at endpoints | abs(sampled *P* − *P*₀) at endpoints |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R8a hoeffding | 0, 1, 2, 3, 4, 5, 8, 9, 10, 11 | 18 | 1–5 | 10/10 | 1 | 0 | 3.261539 | 0 | 0 | 0 |
| R8a oracle | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 | 200 | 20 | 0/10 | 1 | 0 | 1.108155 | 0 | 0 | 0 |
| E8a hoeffding | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 | 87 | 3–15 | 10/10 | 1 | 0 | 2.717949 | 0 | 0 | 0.492188 |
| E8a oracle | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 | 200 | 20 | 0/10 | 1 | 0 | 0.972242 | 0 | 0 | 0.492188 |
| W8a hoeffding | 0, 1, 2, 4, 7, 8, 10, 11, 12, 13 | 32 | 2–4 | 10/10 | 0.058594–1 | 0 | 5.979487 | 0–0.894531 | 0–0.941406 | 0.035156–0.90625 |
| W8a oracle | 0, 3, 4, 5, 6, 7, 8, 10, 13, 19 | 11 | 1–2 | 10/10 | 0.054688–0.472656 | 2–4 | 2.229444 | unmeasured (time-capped, 1–2 optima) | 0.039062–0.339844 | 0.039062–0.378906 |

Sampled bands are the first ten OPTIMAL bands in seed order, excluding timeouts.
The original Hoeffding sampling used the same selection rule, including its
recorded supplemental bands. On W8a the excluded Hoeffding incumbents have
κ = 6–8, more complex than the typical κ* = 4 proved bands; the oracle
timeouts have incumbents κ = 18–22. This selection limits what sampled
success values describe. Sampling retains the 300 s cap and maximum 20 optima;
medians are procedural and the procedure is not uniform sampling.

W8a oracle sampling hit the cap on every band and found only 1–2 optima.
The within-band spread of *P* is therefore unmeasured for W8a oracle; equal
saved scores do not establish a zero spread or uniqueness. Its saved sampled
*P* values 0.054688–0.472656 have 2–4 certified traps at resolution 2.229444.
The earlier W8a Hoeffding run did observe a spread on seed 1, as the table shows;
that observation also fails the grid resolution eligibility check.

The following are time-capped FEASIBLE incumbents, explicitly **non-optimal**.
Their κ and *P* are reported separately and never substituted for κ* or an
optimal-band basin prediction. Their two absolute errors are incumbent measurements.
Exact source rows are in the six linked CSVs above.

| Instance / band | Seed | Status | Certified LB | Incumbent κ | *P* incumbent | *P*₀ | `P0_res` | `n_traps_cert` | `resolution` | abs(*P* incumbent − `P0_res`) | abs(*P* incumbent − *P*₀) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R8a hoeffding | 6 | FEASIBLE, non-optimal | 10 | 12 | 1 | 1 | 1 | 0 | 3.261539 | 0 | 0 |
| R8a hoeffding | 7 | FEASIBLE, non-optimal | 10 | 12 | 1 | 1 | 1 | 0 | 3.261539 | 0 | 0 |
| W8a hoeffding | 3 | FEASIBLE, non-optimal | 4 | 8 | 0.367188 | 0.09375 | 1 | 0 | 5.979487 | 0.632812 | 0.273438 |
| W8a hoeffding | 5 | FEASIBLE, non-optimal | 4 | 6 | 1 | 0.09375 | 1 | 0 | 5.979487 | 0 | 0.90625 |
| W8a hoeffding | 6 | FEASIBLE, non-optimal | 4 | 6 | 1 | 0.09375 | 1 | 0 | 5.979487 | 0 | 0.90625 |
| W8a hoeffding | 9 | FEASIBLE, non-optimal | 4 | 6 | 1 | 0.09375 | 1 | 0 | 5.979487 | 0 | 0.90625 |
| W8a hoeffding | 16 | FEASIBLE, non-optimal | 6 | 8 | 0.378906 | 0.09375 | 1 | 0 | 5.979487 | 0.621094 | 0.285156 |
| W8a oracle | 1 | FEASIBLE, non-optimal | 18 | 20 | 0.265625 | 0.09375 | 0.394531 | 3 | 2.229444 | 0.128906 | 0.171875 |
| W8a oracle | 2 | FEASIBLE, non-optimal | 16 | 20 | 0.277344 | 0.09375 | 0.394531 | 3 | 2.229444 | 0.117188 | 0.183594 |
| W8a oracle | 9 | FEASIBLE, non-optimal | 18 | 22 | 0.152344 | 0.09375 | 0.394531 | 4 | 2.229444 | 0.242188 | 0.058594 |
| W8a oracle | 11 | FEASIBLE, non-optimal | 16 | 18 | 0.265625 | 0.09375 | 0.394531 | 3 | 2.229444 | 0.128906 | 0.171875 |
| W8a oracle | 12 | FEASIBLE, non-optimal | 16 | 18 | 0.257812 | 0.09375 | 0.394531 | 3 | 2.229444 | 0.136719 | 0.164062 |
| W8a oracle | 14 | FEASIBLE, non-optimal | 18 | 20 | 0.089844 | 0.09375 | 0.394531 | 3 | 2.229444 | 0.304688 | 0.003906 |
| W8a oracle | 15 | FEASIBLE, non-optimal | 14 | 20 | 0.160156 | 0.09375 | 0.394531 | 2 | 2.229444 | 0.234375 | 0.066406 |
| W8a oracle | 16 | FEASIBLE, non-optimal | 18 | 20 | 0.5 | 0.09375 | 0.394531 | 2 | 2.229444 | 0.105469 | 0.40625 |
| W8a oracle | 17 | FEASIBLE, non-optimal | 12 | 20 | 0.332031 | 0.09375 | 0.394531 | 3 | 2.229444 | 0.0625 | 0.238281 |
| W8a oracle | 18 | FEASIBLE, non-optimal | 18 | 20 | 0.257812 | 0.09375 | 0.394531 | 4 | 2.229444 | 0.136719 | 0.164062 |

### Section 6.3: seven completed timeout probes

| Instance | Seed | `LB_region` / unchanged LB | Original incumbent κ | Outcome | Cap (s) | Wall (s) |
| --- | --- | --- | --- | --- | --- | --- |
| R8a | 6 | 10 / 10 | 12 | UNKNOWN | 1800 | 1800.225 |
| R8a | 7 | 10 / 10 | 12 | UNKNOWN | 1800 | 1800.316 |
| W8a | 3 | 4 / 4 | 8 | UNKNOWN | 1800 | 1800.301 |
| W8a | 5 | 4 / 4 | 6 | UNKNOWN | 1800 | 1800.330 |
| W8a | 6 | 4 / 4 | 6 | UNKNOWN | 1800 | 1800.307 |
| W8a | 9 | 4 / 4 | 6 | UNKNOWN | 1800 | 1800.327 |
| W8a | 16 | 6 / 6 | 8 | UNKNOWN | 1800 | 1800.298 |

All seven probes returned UNKNOWN at the unchanged 1800 s cap, with no new
solution and unchanged certified bounds. Each used Formulation A, separate
c₀ = *k*_min and c₂ = *k*_max constraints, the saved incumbent hint, the original
seed and eight workers. None was skipped. Whether `LB_region` is exact on
these bands is unresolved. Original FEASIBLE records remain intact; UNKNOWN
does not prove optimality or infeasibility. See the exact
[JSON records](timeout-probe-v1.8.4.json) and [CSV](timeout-probe-v1.8.4.csv).

### Grid choices and gate evidence

The monotone grid rule chooses E8a 16, E8b 16, W8a 32, W8b 48 and R8a 16:
a size must pass along with every larger tested size. W8b's pass at 24 is
insufficient because 32 fails. These choices are recorded without starting E2
or Stage 2. Caps, seeds, thresholds and all completed count, sampling and probe
units are preserved. The [v1.8.4 gate](stage1-gate-v1.8.4.json) records the
six section 6.5 checks and the source digest recomputed from committed source.

Stage 1 shows that band resolution controls which minima remain visible: R8a
oracle recovers κ_true = 16, while E8a keeps κ* = 8 and reports *P* = `P0_res` = 1
against *P*₀ = 0.508, with zero certified traps and resolutions 2.717949/0.972242.
W8a oracle has 2–4 certified traps at resolution 2.229444, proving *P*₀ < 1
under coverage, but its *m* = 16 grid fails resolution, so no basin-prediction
conclusion is drawn. W8a oracle within-band spread remains unmeasured after
time-capped sampling of 1–2 optima. All seven probes are UNKNOWN; whether
`LB_region` is exact on those bands remains unresolved. No Stage 2 work was done.
