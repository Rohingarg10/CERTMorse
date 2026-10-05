"""Saved-artifact basin scoring, never a count solve (v1.8.4 section 3)."""
import json
from pathlib import Path
import numpy as np

from .complex import TorusComplex
from .instances import load_instance
from .landscape import field_diagnostics
from .metrics import basin_probability
from .minima import persistence_pairs, true_basins, resolved_probability, certified_traps
from .raw import write_json
from .units import Unit


def score_arrays(arrays, row, sampling=None):
    cx = TorusComplex(row['grid_m']); inst = load_instance(row['instance'])
    lower, upper, truth = arrays['lower'], arrays['upper'], arrays['truth']
    widths = upper-lower
    w_max, w_med = float(widths.max()), float(np.median(widths))
    resolution = 2*w_max
    pairs, labels = persistence_pairs(truth, cx), true_basins(truth, cx)
    traps = certified_traps(lower, upper, inst.W, cx)
    P0 = resolved_probability(truth, inst.W, cx, 0, pairs=pairs, labels=labels)
    assert P0 == row['P0'], (row['instance'], row['seed'], P0, row['P0'])
    P0_res = resolved_probability(truth, inst.W, cx, w_med, pairs=pairs, labels=labels)
    kappa = row.get('kappa_opt')
    result = dict(row)
    result.pop('P_possible', None)
    P_first, possible = basin_probability(arrays['y'], arrays['mean'], inst.W, cx, lower, upper)
    result['P_possible_simplest'] = possible if kappa is not None else None
    result['P_possible_incumbent'] = possible if kappa is None else None
    optima = arrays.get('optima', np.empty((0, len(cx.pairs)), dtype=np.int8)) if sampling is None else sampling
    values = [basin_probability(y, arrays['mean'], inst.W, cx, lower, upper)[0] for y in optima]
    if kappa is not None:
        result['P_first'] = P_first
        if len(values):
            result.update(P_med=float(np.median(values)), P_lo=min(values), P_hi=max(values), n_opt_found=len(values))
        P = result.get('P_med') if result.get('P_med') is not None else P_first
        result['P'] = P
        result['P_incumbent'] = None
    else:
        result['P'] = None
        result['P_incumbent'] = P_first
        P = P_first
    result.update(w_max=w_max, w_med=w_med, resolution=resolution, n_traps_cert=len(traps),
                  P0_below_1_certified=bool(traps), trivial=(kappa if kappa is not None else row['kappa_cert']) == 4,
                  kappa_ratio=None if kappa is None or row.get('kappa_true') is None else kappa/row['kappa_true'],
                  n_min_true=field_diagnostics(truth, cx)['strict_minima'],
                  n_min_visible=sum(pair.persistence > resolution for pair in pairs),
                  P0_res=P0_res, P0_res_guaranteed=resolved_probability(truth, inst.W, cx, resolution, pairs=pairs, labels=labels),
                  abs_P_minus_P0_res=abs(P-P0_res) if kappa is not None else None,
                  abs_P_minus_P0=abs(P-P0) if kappa is not None else None,
                  abs_P_incumbent_minus_P0_res=abs(P-P0_res) if kappa is None else None,
                  abs_P_incumbent_minus_P0=abs(P-P0) if kappa is None else None)
    assert P_first <= possible
    return result


def score_folder(folder, row, *, sampling_folder=None, root='results/stage1-scoring-v1.8.4'):
    folder = Path(folder)
    inputs = {'matching': folder/'matching.npz'}
    for name in ('measurement.json', 'solve.json', 'bounds.json', 'timing.json'):
        if (folder/name).is_file():
            inputs[name] = folder/name
    if sampling_folder is not None:
        inputs['samples'] = Path(sampling_folder)/'samples.npz'
        record_name = 'sampling.json' if (Path(sampling_folder)/'sampling.json').exists() else 'measurement.json'
        inputs['sampling_record'] = Path(sampling_folder)/record_name
    unit = Unit('scoring', dict(instance=row['instance'], seed=row['seed'], grid_m=row['grid_m'],
                                band_mode=row['band_mode'], base_record=row), inputs, root=root)
    def run(work):
        with np.load(inputs['matching']) as data:
            arrays = {key: data[key] for key in data.files}
        sampling = None
        base = dict(row)
        if sampling_folder is not None:
            with np.load(inputs['samples']) as data:
                sampling = data['optima']
            record = json.loads(inputs['sampling_record'].read_text(encoding='utf-8'))
            base['sampling_status'] = record.get('sampling_status', record.get('status'))
        scored = score_arrays(arrays, base, sampling)
        write_json(work/'measurement-v1.8.4.json', scored)
    path = unit.run(run)
    return json.loads((path/'measurement-v1.8.4.json').read_text(encoding='utf-8')), path
