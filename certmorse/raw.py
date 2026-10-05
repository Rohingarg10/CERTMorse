"""Raw solve, sample and field artefacts, independent of scoring definitions."""
from dataclasses import asdict
import json
from pathlib import Path
import numpy as np

from .complex import TorusComplex, lower_star_gradient
from .forman import witness, NegativeCycle, is_discrete_morse
from .mip import build_A, solve
from .mip.milp import SolveResult
from .mip.solvers import sample_optima, emit_highs
from .rng import streams
from .scaling import choose_scale, model_band, cell_band
from .units import Unit, test_pause, complete_unit

TIME_LIMIT_S = 600
THREADS = 8
MAX_OPTIMA = 20
SAMPLING_CAP_S = 300


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False)+'\n', encoding='utf-8', newline='\n')


def save_arrays(path, seed, **arrays):
    class Writer:
        def __init__(self, stream):
            self.stream = stream
            self.first = True
        def __getattr__(self, name):
            return getattr(self.stream, name)
        def write(self, data):
            result = self.stream.write(data)
            if self.first:
                self.first = False
                self.stream.flush()
                test_pause('file-write', seed)
            return result
    with Path(path).open('wb') as stream:
        np.savez_compressed(Writer(stream), **arrays)


def result_record(result):
    return {key: value for key, value in asdict(result).items() if key not in ('x', 'y', 'wall_s')}


def rehydrate(folder):
    folder = Path(folder)
    if not complete_unit(folder):
        raise ValueError('incomplete solve artefacts cannot be read')
    record = json.loads((folder/'solve.json').read_text(encoding='utf-8'))
    record['wall_s'] = json.loads((folder/'timing.json').read_text(encoding='utf-8'))['wall_s']
    with np.load(folder/'matching.npz') as data:
        return SolveResult(**record, x=data['x'], y=data['y'])


def solve_band(band, config, *, root='results/units-v1.8.4', incumbent=None):
    inputs = {'band': band}
    if incumbent is not None:
        inputs['incumbent'] = incumbent
    resolved = dict(grid_m=16, seed=0, solver='cpsat', formulation='A', time_limit_s=TIME_LIMIT_S,
                    threads=THREADS, warm_start=True, region_probe=False)
    resolved.update(config)
    unit = Unit('solve', resolved, inputs, root=root)
    def run(work):
        cx = TorusComplex(resolved['grid_m'])
        with np.load(band) as data:
            arrays = {key: data[key] for key in data.files}
        lower, upper = arrays['lower'], arrays['upper']
        if 'cell_lo' not in arrays:
            scale, widened = choose_scale(lower, upper)
            vlo, vhi = model_band(lower, upper, scale)
            lo, hi = cell_band(vlo, vhi, cx)
            arrays.update(cell_lo=lo, cell_hi=hi, scale=scale, n_widened=widened)
        lo, hi = arrays['cell_lo'], arrays['cell_hi']
        model = build_A(lo, hi, cx)
        if incumbent:
            with np.load(incumbent) as data:
                hint = dict(y=data['y'], x=data['x'], seed=resolved['seed'])
        else:
            mid = (lo[:cx.nv]+hi[:cx.nv])/2
            a, b = lower_star_gradient(mid, cx)
            x = witness(a, b, lo, hi, cx)
            assert not isinstance(x, NegativeCycle)
            hint = dict(y=np.concatenate((a, b)), x=x, seed=resolved['seed'])
            if resolved['warm_start']:
                from .export_vtk import export_complex
                from .landscape import BETA_PERIODS
                from .mip.warm_start import simplified_hint
                scale = int(arrays.get('scale', 1000))
                export_complex(cx, work/'band.vtu', {'Scalar': mid/scale, 'Lower': lo[:cx.nv]/scale, 'Upper': hi[:cx.nv]/scale}, beta_period=BETA_PERIODS['a'], qaoa=True)
                delta = float(np.min((hi[:cx.nv]-lo[:cx.nv])/(2*scale)))
                candidate, warm_status = simplified_hint(work/'band.vtu', work/'simplified.csv', 2*delta, lo, hi, cx)
                if candidate is not None and candidate['y'].sum() >= hint['y'].sum():
                    hint = dict(**candidate, seed=resolved['seed'])
                write_json(work/'warm-start.json', dict(status=warm_status, used='ttk_simplified' if candidate is not None else 'midpoint'))
        if resolved['region_probe']:
            # c0=k_min and c2=k_max, separately (Euler then fixes kappa).
            nve = len(cx.pairs_ve)
            model.cuts.extend([
                ({p: 1 for p in range(nve)}, cx.nv-len(model.regions.minimum_regions), cx.nv-len(model.regions.minimum_regions)),
                ({p: 1 for p in range(nve, len(cx.pairs))}, cx.nt-len(model.regions.maximum_regions), cx.nt-len(model.regions.maximum_regions)),
            ])
            model.target_matches = (cx.nc-model.regions.LB_region)//2
        emit_highs(model).writeModel(str(work/'model.mps'))
        result = solve(model, resolved['solver'], resolved['time_limit_s'], resolved['threads'], hint, str(work/'solver.log'))
        if result.y is not None:
            a, b = cx.split_matching(result.y)
            assert not isinstance(witness(a, b, lo, hi, cx), NegativeCycle)
            assert is_discrete_morse(result.x, a, b, cx)[0]
            assert model.regions.LB_region <= result.kappa_incumbent
        record = result_record(result)
        record.update(LB_region=model.regions.LB_region, region_minima=len(model.regions.minimum_regions),
                      region_maxima=len(model.regions.maximum_regions))
        # Rehydration uses only SolveResult fields; keep bound metadata separate.
        write_json(work/'solve.json', result_record(result))
        write_json(work/'timing.json', dict(wall_s=result.wall_s))
        write_json(work/'bounds.json', {key: record[key] for key in ('LB_region', 'region_minima', 'region_maxima')})
        arrays.update(x=result.x if result.x is not None else np.array([], dtype=np.int64),
                      y=result.y if result.y is not None else np.array([], dtype=np.int8))
        save_arrays(work/'matching.npz', resolved['seed'], **arrays)
    return unit.run(run)


def sample_band(solve_folder, config, *, root='results/units-v1.8.4', legacy=False):
    solve_folder = Path(solve_folder)
    if not legacy and not complete_unit(solve_folder):
        raise ValueError('incomplete solve artefacts cannot be sampled')
    inputs = {'matching': solve_folder/'matching.npz', 'solve_record': solve_folder/('measurement.json' if legacy else 'solve.json')}
    resolved = dict(grid_m=16, seed=0, max_optima=MAX_OPTIMA, time_cap_s=SAMPLING_CAP_S)
    resolved.update(config)
    unit = Unit('sampling', resolved, inputs, root=root)
    def run(work):
        cx = TorusComplex(resolved['grid_m'])
        with np.load(solve_folder/'matching.npz') as data:
            arrays = {key: data[key] for key in data.files}
        if legacy:
            record = json.loads((solve_folder/'measurement.json').read_text(encoding='utf-8'))
            initial = SolveResult(**{key: record.get(key) for key in SolveResult.__dataclass_fields__ if key not in ('x', 'y')}, x=arrays['x'], y=arrays['y'])
        else:
            initial = rehydrate(solve_folder)
        assert initial.status == 'OPTIMAL'
        model = build_A(arrays['cell_lo'], arrays['cell_hi'], cx)
        samples, status = sample_optima(model, initial.kappa_opt, resolved['max_optima'], resolved['time_cap_s'],
                                       streams(resolved['seed'])['fc'], initial_result=initial, log_path=str(work/'sampling.log'))
        save_arrays(work/'samples.npz', -1, optima=np.array([sample.y for sample in samples], dtype=np.int8))
        write_json(work/'sampling.json', dict(status=status, n_opt_found=len(samples)))
    return unit.run(run)
