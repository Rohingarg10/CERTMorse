# Stage 1 measured costs

Recorded 4 October 2026 on the hardware in ENVIRONMENT.md. Each solver and
model inference requests eight threads. These measurements replace assumptions
for planning; the supplied spec's Appendix E has not been edited.

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
