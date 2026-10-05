"""Record the installed environment and actual TTK discovery output."""
import importlib.metadata as metadata
import json
import platform
from pathlib import Path

hardware=json.loads(Path('.tools/hardware.json').read_text(encoding='utf-8-sig'))
ttk=json.loads(Path('docs/ttk-discovery.json').read_text(encoding='utf8'))
smoke=json.loads(Path('docs/tsfm-smoke.json').read_text(encoding='utf8'))
text=f'''# Environment recorded 4 October 2026

Windows, Python core {platform.python_version()}. CPU:
{hardware['cpu']['Name']} ({hardware['cpu']['NumberOfCores']} cores,
{hardware['cpu']['NumberOfLogicalProcessors']} logical processors).
Installed RAM: {hardware['system']['TotalPhysicalMemory']/2**30:.2f} GiB.
All solver and model-inference runs request eight threads. No GPU is used.

## Core packages

'''
for package in ['qiskit','qiskit-aer','numpy','scipy','networkx','ortools','highspy','vtk','gudhi','hypothesis','pytest']:
    text+=f'- {package}: {metadata.version(package)}\n'
text+='''
The full core freeze is requirements.txt. Separate TimesFM packages are frozen
in requirements-tsfm.txt. Conda-forge TTK 1.3.0, ParaView 5.13.3 and its Python
3.13 interpreter are locked in requirements-ttk.txt. TTK uses the plugin DLL
under venv-ttk/Library/bin/plugins/TopologyToolKit. Windows package extraction
needed a temporary drive alias because conda-forge paths exceeded MAX_PATH.
Setup removes that alias afterwards. Both the environment root and Library/bin
must be on the subprocess PATH to resolve the Python and ParaView DLLs.

## Licenses

Project code: MIT. TTK: BSD. TimesFM source: Apache-2.0. TimesFM 3.0 weights:
timesfm-non-commercial-license-v1.0; downloaded to an ignored local cache and
not redistributed. No Gurobi license has been requested or installed; requesting
a named-user license requires the user's account information. CP-SAT and HiGHS
are the available Stage 1 backends.

## Verified TimesFM CPU integration

'''
text+=f"Checkpoint: {smoke['checkpoint']}. T17 passed. Load: {smoke['model_load_s']:.3f} s; batch of 64 contexts, k=40, horizon=80, three trials: {smoke['batch64_k40_h80_s']}; median {smoke['batch64_median_s']:.3f} s.\n"
text+='''
The PyTorch TimesFM3Evaluator accepts device="cpu". Context shape, exact/shot
covariate shapes, forecast/quantile shapes, finiteness and repeated-batch
determinism were checked. The wrapper uses the cached checkpoint offline.
The measured R8a m=32 depolarizing density-matrix landscape took 5.267 s.
Its CP-SAT count solve reached the 600 s cap (601.474 s including construction
and checking), returning FEASIBLE with kappa_lb=16 and no proven optimum.
Full-size budget extrapolations remain pending; the original estimates are not
presented as measurements. See COMPUTE.md and benchmark.json.

## TTK discovery and decoding contract

Raw properties and example pairs: docs/ttk-discovery.json. Actual CSV headers
and arrays from the installed filters follow. Presence and a successful task
invocation are separate checks. ttkPeriodicGrid is unavailable, so all numerical
cross-checks use the explicit torus VTU.

'''
for name,entry in ttk['filters'].items():
    text+=f"### {name}\n\nAvailable: {entry['available']}.\n\n"
    for key in ['point_arrays','cell_arrays','csv_header','ports','error']:
        if key in entry: text+=f"{key}: `{entry[key]}`\n\n"
text+='''
Persistence cell arrays are PairIdentifier, PairType, Persistence, Birth,
IsFinite. The reader discards the artificial diagonal PairType=-1 and decodes
one essential class per IsFinite=0 cell: PairType 0,1,2 gives its dimension,
Birth its birth, and infinite death. Displayed finite endpoints do not decide
essentiality. On the two-minimum field there is one finite H0 pair plus one
essential H0 class. The spec's §4.3 sentence expecting two finite H0 pairs for
two minima should be corrected; it contradicts T24 and the persistence contract.

All 20 smooth-field persistence comparisons and critical-count comparisons
passed. Mandatory components use four output ports and servermanager.Fetch's
explicit idx argument; passing an OutputPort object alone fetches port zero in
this ParaView version. Near-zero-band minima agree with the exact count.

Aer parameter_binds result indexing was checked through symmetry and repeated
runs. Ideal landscapes agree with the closed form and independent NumPy
implementation on all 12 instances at m=16. The full noisy m=16 symmetry and
off-grid periodicity sweeps passed 60 tests on all 12 instances (66.17 s).
'''
Path('docs/ENVIRONMENT.md').write_text(text,encoding='utf-8', newline='\n')
