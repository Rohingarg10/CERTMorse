"""T9/T11 on every saved Stage 1 count, including non-optimal incumbents."""
import json
from pathlib import Path

import numpy as np

from certmorse.complex import TorusComplex, lower_star_gradient
from certmorse.forman import NegativeCycle, is_discrete_morse, witness
from certmorse.legacy_scores import ROOT, stage1_folders
from certmorse.metrics import critical_counts


def test_T9_T11_all_120_saved_count_bounds_and_morse_solutions():
    records = [(folder, row) for folder, row in stage1_folders()]
    completion = json.loads((ROOT/'docs/oracle-completion-v1.8.4.json').read_text(encoding='utf-8'))
    for instance in ('E8a', 'W8a'):
        for band in completion['records'][instance]['bands']:
            row = json.loads((Path(band['scoring'])/'measurement-v1.8.4.json').read_text(encoding='utf-8'))
            records.append((Path(band['raw']), row))
    assert len(records) == 120
    for folder, row in records:
        cx = TorusComplex(row['grid_m'])
        with np.load(folder/'matching.npz') as data:
            lo, hi, y, x = (data[key] for key in ('cell_lo', 'cell_hi', 'y', 'x'))
            incumbent = cx.nc-2*int(y.sum())
            midpoint = (lo[:cx.nv]+hi[:cx.nv])/2
            ma, mb = lower_star_gradient(midpoint, cx)
            assert not isinstance(witness(ma, mb, lo, hi, cx), NegativeCycle), (folder, 'midpoint')
            midpoint_count = cx.nc-2*int(ma.sum()+mb.sum())
            assert row['kappa_lb'] <= incumbent <= midpoint_count, (folder, row['kappa_lb'], incumbent, midpoint_count)
            if row['ttk_warm_status'] == 'accepted':
                assert incumbent <= row['ttk_warm_count'], (folder, incumbent, row['ttk_warm_count'])
            a, b = cx.split_matching(y)
            assert is_discrete_morse(x, a, b, cx)[0], folder
            assert not isinstance(witness(a, b, lo, hi, cx), NegativeCycle), folder
            c0, c1, c2 = critical_counts(y, cx)
            assert c0 >= 1 and c1 >= 2 and c2 >= 1 and c1 == c0+c2, (folder, c0, c1, c2)
            assert c0+c1+c2 == incumbent == row['kappa_incumbent'], folder
            for count in (row['kappa_lb'], row['kappa_cert'], incumbent, midpoint_count, c0+c1+c2):
                assert count % 2 == 0, (folder, count)
