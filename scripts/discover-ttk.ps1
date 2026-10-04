$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'env.ps1')
New-Item -ItemType Directory -Force docs,results/stage1 | Out-Null
& (Join-Path (Split-Path -Parent $PSScriptRoot) 'venv-core\Scripts\python.exe') -c "import numpy as np; from certmorse.complex import TorusComplex; from certmorse.export_vtk import export_complex; c=TorusComplex(16); v=np.arange(c.nv); g=np.cos(4*np.pi*(v%16)/16)+np.cos(2*np.pi*(v//16)/16); export_complex(c,'results/stage1/discovery.vtu',{'Scalar':g,'Lower':g-.01,'Upper':g+.01})"
if ($LASTEXITCODE -ne 0) { throw "VTU generation exited $LASTEXITCODE" }
& $env:CERTMORSE_PVPYTHON ttk_scripts/discovery.py --in results/stage1/discovery.vtu --out docs/ttk-discovery.json
if ($LASTEXITCODE -ne 0) { throw "TTK discovery exited $LASTEXITCODE" }
