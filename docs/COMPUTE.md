# Stage 1 measured costs

Recorded 4 October 2026 on the hardware in ENVIRONMENT.md. Each solver and
model inference requests eight threads. These measurements replace assumptions
for planning; the original planning estimates have not been edited.

| Work | Measured wall time | Outcome |
|---|---:|---|
| R8a density-matrix field, m=32, depolarizing | 5.267 s | Complete deterministic field |
| Its CP-SAT A solve, N=1000 band | 601.474 s | FEASIBLE at 600 s cap; count lower bound 16; no kappa* |
| TimesFM CPU load | 2.933 s | Checkpoint loaded from local cache |
| 64 TimesFM forecasts, k=40, horizon=80 | median 4.056 s | Three trials; T17 passed |
| R8a m=16 A count solves, 20 bands | about 1.2–2.1 s each | All OPTIMAL, kappa*=32 |
| HiGHS A, m=16 perfect-Morse narrow band | 9.221 s | OPTIMAL, count 4; benchmark only |
| Full noisy-landscape test sweep | 66.17 s | 60 passed |
| 20 TTK count/persistence comparisons plus T7 | 51.80 s | Passed |

The m=32 solve establishes that count optimization, rather than exact circuit
evaluation, can dominate this workload. A timeout is an incumbent/bound
sandwich and must not be turned into an optimum. The isolated m=16 and m=32
results do not justify multiplying by grid size to forecast every configuration.
Three repeated solver timings and the full planned sweep remain necessary
before replacing Appendix E's total-hour ranges with measured totals.

## Corrected v1.7 pilots

Three repeated solves of the same m=32 depolarizing/oracle band at a
60-second search cap returned FEASIBLE, count bound 4 and incumbent 32 in every
trial. The median total solver wall time was 61.074 s. Each solve used a
witness-verified 32-cell TTK simplification hint. These short-cap pilots have no
proven optimum and do not replace the original 600-second measurement, whose
raw solver incumbent is 36 and count bound is 16. The revised benchmark driver
retains the incumbent, gap, node count, budget and per-trial status.

The pilots ran alongside Stage 1 verification; their wall times are not isolated
throughput measurements. They establish useful partial-result behavior and
stronger feasible starts, not a calibrated speedup ratio or total Stage 2 hours.
Details: benchmark-v1.7.json. Larger-grid execution should use explicit caps and
retain unresolved gaps; a full experiment budget needs a separate measured pilot.

The additional m=16 R8a Hoeffding-band pilot reached the 600-second cap in
600.564 seconds, returning FEASIBLE with count bound 4 and incumbent 20.
Its simplification candidate failed the cell-band witness, so the midpoint
fallback was used. UB_pers=18 remains a reference. Wider guaranteed bands can
require substantially more search than the oracle fixtures. The recorded
measurement is stage1-r8a-v1.7-hoeffding.csv.
