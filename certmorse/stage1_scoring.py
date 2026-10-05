"""Derived rows for the missing Stage 1 bands; count artefacts remain raw."""
import json
from pathlib import Path
import numpy as np

from .complex import TorusComplex, lower_star_gradient
from .forman import witness, NegativeCycle
from .landscape import field_diagnostics
from .metrics import critical_counts
from .mip.bounds import persistence_bounds
from .persistence import persistence, lower_star_values, bottleneck
from .raw import rehydrate
from .scoring import score_arrays
from .ttk import read_mandatory
from .units import Unit
from .raw import write_json


def oracle_row(folder, reference, *, sampling_folder=None):
    folder = Path(folder)
    inputs = {name: folder/name for name in ('matching.npz', 'solve.json', 'bounds.json',
              'timing.json', 'warm-start.json', 'mandatory.csv')}
    if sampling_folder is not None:
        inputs.update(samples=Path(sampling_folder)/'samples.npz', sampling=Path(sampling_folder)/'sampling.json')
    unit = Unit('scoring', dict(operation='oracle_completion', reference=reference), inputs,
                root='results/stage1-completion-scoring-v1.8.4')
    def run(work):
        with np.load(inputs['matching.npz']) as data:
            arrays = {key: data[key] for key in data.files}
        result = rehydrate(folder)
        assert result.y is not None, result.status
        cx = TorusComplex(reference['grid_m'])
        row = dict(reference)
        # These belong to the old band or its old solve, never the new band.
        for key in list(row):
            if key.startswith('P_') or key.startswith('abs_P') or key.startswith('kappa_'):
                del row[key]
        row.pop('multiplicity_run_path', None)
        bounds = json.loads(inputs['bounds.json'].read_text(encoding='utf-8'))
        warm = json.loads(inputs['warm-start.json'].read_text(encoding='utf-8'))
        scale = int(arrays['scale'])
        lo, hi = arrays['cell_lo'], arrays['cell_hi']
        mid = (lo[:cx.nv]+hi[:cx.nv])/(2*scale)
        refs = persistence_bounds(mid, lo[:cx.nv]/scale, hi[:cx.nv]/scale, cx)
        diagnostics = field_diagnostics(arrays['truth'], cx, scale)
        assert diagnostics['ties_exact'] == 0, 'do not repeat a saved zero-band count solve'
        true_a, true_b = lower_star_gradient(arrays['truth'], cx)
        true_count = cx.nc-2*int(true_a.sum()+true_b.sum())
        assert true_count == reference['kappa_true']
        transfer = not isinstance(witness(true_a, true_b, lo, hi, cx), NegativeCycle)
        covered = bool(np.all((arrays['lower'] <= arrays['truth']) & (arrays['truth'] <= arrays['upper'])))
        if covered and diagnostics['sep_min_units'] >= 14:
            assert transfer
        counts, _ = read_mandatory(inputs['mandatory.csv'])
        mandatory = max(4, 2*(counts['MinimumComponents']+counts['MaximumComponents']))
        c0, c1, c2 = critical_counts(result.y, cx)
        assert c0 >= 1 and c2 >= 1 and c1 == c0+c2
        row.update(run_id=folder.name, raw_unit_id=folder.name, sampling_unit_id=None, status=result.status,
                   kappa_lb=result.kappa_lb, kappa_incumbent=result.kappa_incumbent,
                   kappa_opt=result.kappa_opt, kappa_cert=max(result.kappa_lb, bounds['LB_region']),
                   kappa_true=true_count, kappa_zero=None, kappa_zero_scale=None,
                   lb_is_certificate=result.lb_is_certificate, bound=result.bound, gap=result.gap,
                   wall_s=result.wall_s, nodes=result.nodes, cut_iters=result.cut_iters, cuts_added=result.cuts_added,
                   c0=c0, c1=c1, c2=c2, scale=scale, n_widened=int(arrays['n_widened']),
                   coverage=covered, transfer_ok=transfer, transfer_claim=covered and transfer,
                   band_mode='oracle', simultaneous_band_guarantee=False, **diagnostics,
                   sep_min=diagnostics['sep_min_units'], LB_mand=mandatory, **refs, **bounds,
                   warm_start_used=warm['used'], ttk_warm_status=warm['status'], ttk_warm_count=warm['count'],
                   UB_witness_justified=warm['count'] is not None and warm['count'] <= refs['UB_pers'],
                   bound_violation=result.kappa_incumbent < mandatory,
                   P_first=None, P_med=None, P_lo=None, P_hi=None, n_opt_found=0,
                   sampling_status='not_requested' if result.status == 'OPTIMAL' else 'skipped_not_optimal', d_B=None)
        if covered and transfer:
            assert row['kappa_cert'] <= true_count
            assert result.kappa_opt is None or result.kappa_opt <= true_count
        for name in ('kappa_true', 'kappa_incumbent', 'kappa_lb', 'kappa_opt', 'kappa_cert'):
            count = row[name]
            row[name+'_per_copy'] = None if count is None or count % row['copies'] else count//row['copies']
        if result.status == 'OPTIMAL':
            row['d_B'] = bottleneck(persistence(result.x, cx, scale), persistence(lower_star_values(arrays['truth'], cx), cx, 1))
        samples = None
        if sampling_folder is not None:
            with np.load(inputs['samples']) as data:
                samples = data['optima']
            row['sampling_status'] = json.loads(inputs['sampling'].read_text(encoding='utf-8'))['status']
            row['sampling_unit_id'] = Path(sampling_folder).name
        scored = score_arrays(arrays, row, samples)
        write_json(work/'measurement-v1.8.4.json', scored)
    path = unit.run(run)
    return json.loads((path/'measurement-v1.8.4.json').read_text(encoding='utf-8')), path
