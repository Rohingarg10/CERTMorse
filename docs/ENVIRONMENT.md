# Environment recorded 4 October 2026

Windows, Python core 3.11.17. CPU:
Intel(R) Core(TM) Ultra 7 155H (16 cores,
22 logical processors).
Installed RAM: 31.51 GiB.
All solver and model-inference runs request eight threads. No GPU is used.

## Core packages

- qiskit: 2.5.2
- qiskit-aer: 0.17.2
- numpy: 2.4.6
- scipy: 1.17.1
- networkx: 3.6.1
- ortools: 9.15.6755
- highspy: 1.12.0 (qualified v1.7 pin; original v1.6 runs used 1.15.1)
- vtk: 9.7.1
- gudhi: 3.13.0
- hypothesis: 6.168.3
- pytest: 9.1.1

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

Checkpoint: google/timesfm-3.0-pytorch. T17 passed. Load: 2.933 s; batch of 64 contexts, k=40, horizon=80, three trials: [3.919664899993222, 4.056193900003564, 4.46135899994988]; median 4.056 s.

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

### TTKPersistenceDiagram

Available: True.

point_arrays: `['ttkVertexScalarField', 'CriticalType', 'Coordinates']`

cell_arrays: `['PairIdentifier', 'PairType', 'Persistence', 'Birth', 'IsFinite']`

csv_header: `"PairIdentifier","PairType","Persistence","Birth","IsFinite","Cell Type"`

### TTKScalarFieldCriticalPoints

Available: True.

point_arrays: `['CriticalType', 'IsOnBoundary', 'ttkVertexScalarField', 'Scalar', 'Lower', 'Upper', 'Scalar_Order']`

cell_arrays: `[]`

csv_header: `"CriticalType","IsOnBoundary","ttkVertexScalarField","Scalar","Lower","Upper","Scalar_Order","Points:0","Points:1","Points:2"`

### TTKDiscreteGradient

Available: True.

point_arrays: `['CellDimension', 'CellId', 'Scalar', 'IsOnBoundary', 'ttkVertexScalarField']`

cell_arrays: `[]`

csv_header: `"CellDimension","CellId","Scalar","IsOnBoundary","ttkVertexScalarField","Points:0","Points:1","Points:2"`

### TTKMorseSmaleComplex

Available: True.

point_arrays: `['CellDimension', 'CellId', 'Scalar', 'IsOnBoundary', 'ttkVertexScalarField', 'ManifoldSize']`

cell_arrays: `[]`

csv_header: `"CellDimension","CellId","Scalar","IsOnBoundary","ttkVertexScalarField","ManifoldSize","Points:0","Points:1","Points:2"`

### TTKTopologicalSimplification

Available: True.

point_arrays: `['Scalar', 'Lower', 'Upper', 'Scalar_Order']`

cell_arrays: `[]`

csv_header: `"Scalar","Lower","Upper","Scalar_Order","Points:0","Points:1","Points:2"`

### TTKMandatoryCriticalPoints

Available: True.

point_arrays: `['Scalar', 'Lower', 'Upper', 'MinimumComponents']`

cell_arrays: `[]`

csv_header: `"Scalar","Lower","Upper","MinimumComponents","Points:0","Points:1","Points:2"`

ports: `{'0': ['Scalar', 'Lower', 'Upper', 'MinimumComponents'], '1': ['Scalar', 'Lower', 'Upper', 'JoinSaddleComponents'], '2': ['Scalar', 'Lower', 'Upper', 'SplitSaddleComponents'], '3': ['Scalar', 'Lower', 'Upper', 'MaximumComponents']}`

### TTKBottleneckDistance

Available: True.

point_arrays: `[]`

cell_arrays: `[]`

csv_header: `"Coordinates:0","Coordinates:1","Coordinates:2","CriticalType","Points:0","Points:1","Points:2","ttkVertexScalarField"`

### TTKPeriodicGrid

Available: False.

error: `module 'paraview.simple' has no attribute 'TTKPeriodicGrid'`


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
