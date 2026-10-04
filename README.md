# CERTMORSE

Stage 1 implementation of [public method](docs/METHOD.md):
QAOA landscapes, simultaneous confidence bands, torus complexes, lower-star
gradients, exact discrete-Morse witnesses, CP-SAT and HiGHS optimization, and
GUDHI persistence. TTK and TimesFM run in separate environments through files.

The certificate concerns a critical-cell count on a sampled grid, under explicit
coverage and transfer assumptions. Basin locations are predictions. Read
[CERTIFICATE.md](docs/CERTIFICATE.md) for the proof and limitations,
[STAGE1.md](docs/STAGE1.md) for gate evidence, and
[public method](docs/METHOD.md) for current status and
[CORRECTIONS.md](docs/CORRECTIONS.md) for the technical findings and fixes.
Stage 2 has not started; there is no optimizer experiment implementation yet.

From PowerShell in the project directory:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/setup.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/stage1-gate.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/test.ps1 -Component core
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/test.ps1 -Component ttk
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/smoke-tsfm.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/measure-r8a.ps1 -Resume
```

Setup installs project environments and caches. `scripts/env.ps1` configures the
current PowerShell process. Measurement runs save config, status, raw matching,
bands, MPS, and solver logs under `results/`, keyed by canonical config hash,
implementation revision and a digest of the model sources and TTK adapters.
Resume skips complete runs and restarts incomplete runs. Weights and environments
are ignored by Git. The supplied exploratory scripts remain unchanged.

The full gate deliberately repeats the original oracle-band R8a fixture for
comparison. Oracle Gaussian bands are approximate. The operational config
default is Hoeffding; an explicit guaranteed-band measurement uses
`scripts/measure-r8a.ps1 -BandMode hoeffding`. Large-grid pilots can use
`scripts/benchmark-stage1.ps1 -Limit 60 -Repeats 3`; capped results retain their
incumbents and bounds without claiming an optimum.

Code is MIT licensed. TTK is BSD licensed. TimesFM source is Apache-2.0; its 3.0
weights have the TimesFM non-commercial license and are not redistributed.
