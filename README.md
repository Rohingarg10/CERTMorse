# CERTMORSE

CERTMORSE studies depth-one QAOA MaxCut landscapes under shot uncertainty. It
constructs bands on a triangulated parameter torus, finds a band-feasible
discrete Morse function with the fewest critical cells, and checks its matching
with an exact integer witness. Count certificates and combinatorial basin areas
are reported separately, with the limits established by Stage 1.

**Status: Stage 1 complete; Stage 2 planned**

![R8a oracle: saved band, optimal critical cells and combinatorial basins](docs/images/stage1-r8a-oracle.png)

R8a oracle, channel (a), m=16, N=1000, seed 0. All three panels use saved
Stage 1 artifacts; no solve or sampling was repeated. [Figure provenance](docs/images/stage1-r8a-oracle.json).

The Stage 1 table below uses proved OPTIMAL bands for κ* and P ranges. P is a
procedural sampling median when available; timed-out incumbents are reported
separately in [STAGE1.md](docs/STAGE1.md). Sampling selects the first ten OPTIMAL
bands and excludes timeouts. `resolution` is twice the largest full band width;
`P0_res` uses the median full width. Trivial bands have κ*=4 and P=1 by construction.

| Instance / band / exact CSV | OPTIMAL | κ* | κ_true | *P* (reported) | *P*₀ | `P0_res` | `n_traps_cert` | `resolution` | `trivial` (OPTIMAL) | abs(*P* − `P0_res`) | abs(*P* − *P*₀) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [R8a hoeffding](docs/stage1-r8a-hoeffding-rescored-v1.8.4.csv) | 18/20 | 10–12 | 16 | 1 | 1 | 1 | 0 | 3.261539 | 0/18 | 0 | 0 |
| [R8a oracle](docs/stage1-r8a-oracle-completion-rescored-v1.8.4.csv) | 20/20 | 16 | 16 | 1 | 1 | 1 | 0 | 1.108155 | 0/20 | 0 | 0 |
| [E8a hoeffding](docs/stage1-e8a-hoeffding-rescored-v1.8.4.csv) | 20/20 | 8 | 12 | 1 | 0.507812 | 1 | 0 | 2.717949 | 0/20 | 0 | 0.492188 |
| [E8a oracle](docs/stage1-e8a-oracle-completion-rescored-v1.8.4.csv) | 20/20 | 8 | 12 | 1 | 0.507812 | 1 | 0 | 0.972242 | 0/20 | 0 | 0.492188 |
| [W8a hoeffding](docs/stage1-w8a-hoeffding-rescored-v1.8.4.csv) | 15/20 | 4–6 | 48 | 0.414062–1 | 0.09375 | 1 | 0 | 5.979487 | 14/15 | 0–0.585938 | 0.320312–0.90625 |
| [W8a oracle](docs/stage1-w8a-oracle-completion-rescored-v1.8.4.csv) | 10/20 | 14–20 | 48 | 0.054688–0.472656 | 0.09375 | 0.394531 | 2–4 | 2.229444 | 0/10 | 0.039062–0.339844 | 0.039062–0.378906 |

R8a oracle recovers κ_true=16. E8a retains κ*=8, with P=P0_res=1 versus P0≈0.508
because two dimples and their saddles remain unresolved. W8a oracle certifies
2–4 traps under coverage, but its m=16 grid fails adequacy, so no basin-prediction
conclusion is drawn. Its within-band spread is unmeasured after capped sampling
of 1–2 optima. All seven probes are UNKNOWN; LB_region tightness remains
unresolved. No optimizer-success prediction was tested.

If a band covers the true grid field, a minimum with persistence greater than
twice the largest full band width has its own minimum region, and a depth gap
beyond that threshold plus the success tolerance makes it a certified trap.
Under the same coverage condition, any minimum region whose smallest lower
endpoint exceeds the smallest upper endpoint plus the success tolerance
certifies a non-global minimum and proves true discrete-flow success probability
is below one.

Install with Python **3.11** (the checked core environment uses 3.11.17):

```sh
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install --no-deps -e .
```

Quick start, after installation:

```sh
python scripts/quickstart.py
```

This solves one synthetic 3×3 band using CP-SAT and checks the exact witness.
It has a 60 s solve cap, uses one worker, and writes a small report and log to
`results/quickstart/`; success prints `OPTIMAL` and κ*=4. These are demonstration
settings, separate from the unchanged Stage 1 measurement settings.

Core tests use the cleaned `v0.1` release archives. Download
`certmorse-results-v0.1.tar.gz`, `certmorse-archive-v0.1.tar.gz` and their
`.sha256` files into `.release-assets/`, then run:

```sh
python scripts/unpack-release.py .release-assets
python -m pytest -q -p scripts.public_gate_paths -m "not ttk and not tsfm and not gurobi"
```

GitHub Actions is configured to run that core selection on Linux with Python
3.11.17. It needs those four assets attached to the `v0.1` GitHub Release;
the workflow has not been executed locally. TTK and TimesFM are optional
separate environments; Gurobi needs its own licence. TimesFM 3.0 weights are
non-commercial and downloaded at runtime. [THIRD_PARTY.md](THIRD_PARTY.md)
records their terms and dependency licences. The project code is [MIT](LICENSE).

Read [STAGE1.md](docs/STAGE1.md), [CERTIFICATE.md](docs/CERTIFICATE.md), and the
self-contained [public method](docs/METHOD.md). [SANITIZATION.md](SANITIZATION.md)
and [the public gate](docs/stage1-gate-public.json) record the approved cleanup
and unavailable historical checks. Historical hashes remain unchanged.

The public gate reports **BLOCKED** because 17 checks depend on files deliberately
removed or redacted for privacy; every other check passes. Tests and gates never
write tracked evidence: their reports use ignored scratch output, and recording
a gate report is a separate explicit command described in [METHOD.md](docs/METHOD.md).
