"""Render section 6.4 from saved fields and tables; never run a solver."""
import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from certmorse.complex import TorusComplex
from certmorse.instances import load_instance
from certmorse.metrics import BASIN_TOLERANCE
from certmorse.minima import persistence_pairs, resolved_probability

ROOT = Path(__file__).resolve().parents[1]
MARKER = '## v1.8.4 corrections and completion'
TABLES = {
    (name, mode): f'stage1-{name.lower()}-{suffix}-rescored-v1.8.4.csv'
    for name in ('R8a', 'E8a', 'W8a')
    for mode, suffix in (('hoeffding', 'hoeffding'), ('oracle', 'oracle-completion'))
}


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |',
                      '| ' + ' | '.join(['---'] * len(headers)) + ' |'] +
                     ['| ' + ' | '.join(map(str, row)) + ' |' for row in rows])


def number(value):
    return f'{float(value):.6f}'.rstrip('0').rstrip('.')


def span(values):
    values = list(map(float, values))
    lo, hi = min(values), max(values)
    return number(lo) if lo == hi or number(lo) == number(hi) else f'{number(lo)}–{number(hi)}'


def persistence_record():
    records = []
    resolution = read_json(ROOT/'docs/resolution-v1.8.3.json')
    assert len(resolution['rows']) == 20
    for row in resolution['rows']:
        path = ROOT/row['run_path'].replace('\\', '/')/'field.npz'
        with np.load(path) as data:
            field = data['truth'].copy()
        cx = TorusComplex(row['grid_m'])
        W = load_instance(row['instance']).W
        pairs = persistence_pairs(field, cx)
        assert resolved_probability(field, W, cx, 0, pairs=pairs) == row['P0_grid']
        assert resolved_probability(field, W, cx, np.inf, pairs=pairs) == 1
        minima = [dict(minimum=p.minimum, elder=p.elder, birth=p.birth,
                       death=None if np.isinf(p.death) else p.death,
                       persistence=None if np.isinf(p.persistence) else p.persistence,
                       non_global=bool(p.birth > field.min()+BASIN_TOLERANCE*W)) for p in pairs]
        records.append(dict(instance=row['instance'], grid_m=cx.m, field=path.relative_to(ROOT).as_posix(),
                            field_sha256=sha256(path.read_bytes()).hexdigest(), W=W, random_cut=-W/2,
                            tau_min=BASIN_TOLERANCE*W, P0=row['P0_grid'], minima=minima))
    return dict(specification='v1.8.4', saved_fields=20,
                method='six-neighbour lower-star H0 persistence, union-find elder rule', rows=records)


def persistence_text(record):
    rows = []
    for row in record['rows']:
        minima = [p for p in row['minima'] if p['non_global']]
        finite_global = [p['persistence'] for p in row['minima']
                         if not p['non_global'] and p['persistence'] is not None]
        rows.append([row['instance'], row['grid_m'], len(minima),
                     '—' if not minima else span(p['persistence'] for p in minima),
                     '—' if not minima else span(p['birth'] for p in minima), number(row['random_cut']),
                     '—' if not finite_global else span(finite_global)])
    return table(['Instance', '*m*', 'Non-global minima', 'Their persistence', 'Their values',
                  '−*W*/2', 'Finite persistence of global-class minima'], rows)


def render_section(record):
    rows, samples, incumbents = [], [], []
    for (name, mode), filename in TABLES.items():
        with (ROOT/'docs'/filename).open(encoding='utf-8', newline='\n') as stream:
            data = list(csv.DictReader(stream))
        assert len(data) == 20 and [int(r['seed']) for r in data] == list(range(20))
        optimal = [r for r in data if r['status'] == 'OPTIMAL']
        sampled = [r for r in data if int(r['n_opt_found'])]
        label = f'[{name} {mode}]({filename})'
        rows.append([label, f'{len(optimal)}/20', span(r['kappa_opt'] for r in optimal),
                     span(r['kappa_true'] for r in data), span(r['P'] for r in optimal),
                     span(r['P0'] for r in data), span(r['P0_res'] for r in data),
                     span(r['n_traps_cert'] for r in data), span(r['resolution'] for r in data),
                     f"{sum(r['trivial'] == 'True' for r in optimal)}/{len(optimal)}",
                     span(r['abs_P_minus_P0_res'] for r in optimal), span(r['abs_P_minus_P0'] for r in optimal)])
        values = [r[k] for r in sampled for k in ('P_lo', 'P_hi')]
        spread = 'unmeasured (time-capped, 1–2 optima)' if (name, mode) == ('W8a', 'oracle') else span(
            float(r['P_hi'])-float(r['P_lo']) for r in sampled)
        samples.append([f'{name} {mode}', ', '.join(r['seed'] for r in sampled),
                        sum(int(r['n_opt_found']) for r in sampled), span(r['n_opt_found'] for r in sampled),
                        f"{sum(r['sampling_status'] == 'time_capped' for r in sampled)}/{len(sampled)}",
                        span(values), span(r['n_traps_cert'] for r in data),
                        span(r['resolution'] for r in data), spread,
                        span(abs(float(r[k])-float(r['P0_res'])) for r in sampled for k in ('P_lo', 'P_hi')),
                        span(abs(float(r[k])-float(r['P0'])) for r in sampled for k in ('P_lo', 'P_hi'))])
        for r in data:
            if r['status'] == 'OPTIMAL':
                continue
            incumbents.append([f'{name} {mode}', r['seed'], 'FEASIBLE, non-optimal', r['kappa_cert'],
                               r['kappa_incumbent'], number(r['P_incumbent']), number(r['P0']),
                               number(r['P0_res']), r['n_traps_cert'], number(r['resolution']),
                               number(r['abs_P_incumbent_minus_P0_res']), number(r['abs_P_incumbent_minus_P0'])])
    main_table = table(['Instance / band / exact CSV', 'OPTIMAL', 'κ*', 'κ_true', '*P* (reported)',
                        '*P*₀', '`P0_res`', '`n_traps_cert`', '`resolution`', '`trivial` (OPTIMAL)',
                        'abs(*P* − `P0_res`)', 'abs(*P* − *P*₀)'], rows)
    sample_table = table(['Instance / band', 'Selected seeds', 'Optima', 'Per band', 'Time-capped',
                         'Saved sampled *P* values', '`n_traps_cert`', '`resolution`', 'Observed within-band spread',
                         'abs(sampled *P* − `P0_res`) at endpoints', 'abs(sampled *P* − *P*₀) at endpoints'], samples)
    incumbent_table = table(['Instance / band', 'Seed', 'Status', 'Certified LB', 'Incumbent κ', '*P* incumbent',
                            '*P*₀', '`P0_res`', '`n_traps_cert`', '`resolution`',
                            'abs(*P* incumbent − `P0_res`)', 'abs(*P* incumbent − *P*₀)'], incumbents)
    probes = read_json(ROOT/'docs/timeout-probe-v1.8.4.json')['rows']
    probe_table = table(['Instance', 'Seed', '`LB_region` / unchanged LB', 'Original incumbent κ',
                        'Outcome', 'Cap (s)', 'Wall (s)'],
                       [[r['instance'], r['seed'], f"{r['LB_region']} / {r['kappa_lb_v184']}",
                         r['kappa_incumbent_original'], r['status_v184'], r['time_cap_s'], f"{r['wall_s']:.3f}"]
                        for r in probes])
    return f'''{MARKER}

The governing [public method](METHOD.md)
corrects the meaning of *P* and completes the original gate's missing items.
*P* is the success probability of the simplest landscape consistent with the band.
It estimates the true success probability at the band's resolution, `P0_res`;
it is never a certificate. It does not estimate *P*₀ when unresolved minima
remain in the true field. `P_possible` is withdrawn as an ambiguity measure:
it cannot see erased basins. The saved column is `P_possible_simplest`, retained
for continuity with the assertion *P* ≤ `P_possible_simplest`, and used in no conclusion.

### Re-scored Hoeffding and oracle results

All six datasets use *m* = 16, channel (a), *N* = 1000, α = 0.05,
field seed 1003 and band seeds 0–19. Ranges of κ* and *P* here refer only to
proved OPTIMAL bands; trap and resolution ranges cover all twenty bands.
Reported *P* is the procedural median when sampled, otherwise the first-optimum
value; exact `P_first` and sampled ranges remain in the CSVs.
`P0_res` merges minima below the median full reported band width; `resolution`
is twice the maximum full width, the sufficient visibility threshold.
The `trivial` column counts κ* = 4 bands, whose *P* = 1 follows by construction.
Such bands are kept separate from non-trivial RQ2 measurements. Each CSV also
contains `P0_res_guaranteed`, visible-minimum counts and every per-band value.

{main_table}

### Persistence recomputed from the saved fields

The table below was recomputed by union-find with the elder rule on all twenty
saved shot-free resolution fields, using the six-neighbour D5 triangulation.
Non-global means value > min *G* + τ_min, with τ_min = 0.02*W*; the essential
minimum has infinite persistence. Exact pairs, births, deaths and field hashes
are in [persistence-v1.8.4.json](persistence-v1.8.4.json).
Finite global-class pairs are included to make the R8a control comparison explicit.

{persistence_text(record)}

At E8a *m* = 16, the two non-global minima have persistences 0.003656 and
0.015802 and values −5.003218 and −5.009777, beside the random-cut valley
−*W*/2 = −5. At W8b *m* = 48, eight dimples have persistence
0.000016–0.018359 and values −14.737048 to −14.009942; the other ten
have persistence 0.211971–1.111769. These are saved-field measurements.

### Why counts and basin success differ

A wide band allows nearby low points and their separating saddles to disappear
from a simplest consistent field. Once a basin disappears, measuring success
on that field cannot recover its original area. Persistence measures the height
needed to join a minimum to an older component. The proposition in
[CERTIFICATE.md](CERTIFICATE.md#reported-band-resolution-proposition-v184-22)
guarantees a distinct minimum region above persistence 2*w*; it allows shallower
features to disappear. `P0_res` makes the comparison at the band's resolution.

R8a goes from κ* = 10–12 under Hoeffding to κ* = 16 = κ_true under oracle.
Its finite minima persist for 1.567589–1.686092 (about 1.57–1.69), above the
oracle resolution 1.108155 (1.11) and below the Hoeffding resolution 3.261539
(3.26). This is consistent with the narrower oracle bands retaining those minima.
All minima are global-class, so *P* = *P*₀ = `P0_res` = 1 in both modes.

E8a has κ* = 8 in both modes against κ_true = 12. The four missing cells
are the two sub-resolution dimples and their saddles. Thus *P* = `P0_res` = 1
while *P*₀ = 0.5078125 (0.508): there are zero certified traps and the resolutions
are 2.717949 (Hoeffding) and 0.972242 (oracle). The discrepancy is a limit of
what these bands can resolve, even though the grid resolution check passes.

W8a oracle certifies 2–4 traps per band, proving *P*₀ < 1 under band coverage.
Its first-optimum *P* is 0.054688–0.472656, against `P0_res` = 0.394531 and
*P*₀ = 0.093750, at resolution 2.229444. W8a fails the grid resolution check
at *m* = 16, so no basin-prediction conclusion is drawn in either band mode.
The Hoeffding resolution is 5.979487, with zero certified traps; fourteen
proved bands have κ* = 4 and hence *P* = 1 by construction.

### Original gate gaps and section 6.2 completion

The v1.8.3 PASS used an incomplete measurement list: it included only R8a oracle
counts and omitted all oracle multiplicity sampling. It therefore left 40 oracle
counts and 30 sampling runs required by the original gate unfinished. Its E8a
report also failed to compare *P* = 1 with *P*₀ = 0.508 or κ* < κ_true.
The uncommitted-state gap was closed by the section 8 and subsequent commits,
preserving the original `stage1-v1.8.3` tag and pinned digest separately.

Section 6.2 completed the 40 missing counts: E8a 20/20 OPTIMAL; W8a 10/20
OPTIMAL and 10/20 FEASIBLE at 600 s. The twenty R8a oracle counts were reused.
Thirty oracle sampling runs found 411 optima: R8a 200, E8a 200, W8a 11.
The saved [completion records](oracle-completion-v1.8.4.json) and
[hash manifest](completion-evidence-v1.8.4.json) retain every unit and its settings.

### Sampling selection and limits

{sample_table}

Sampled bands are the first ten OPTIMAL bands in seed order, excluding timeouts.
The original Hoeffding sampling used the same selection rule, including its
recorded supplemental bands. On W8a the excluded Hoeffding incumbents have
κ = 6–8, more complex than the typical κ* = 4 proved bands; the oracle
timeouts have incumbents κ = 18–22. This selection limits what sampled
success values describe. Sampling retains the 300 s cap and maximum 20 optima;
medians are procedural and the procedure is not uniform sampling.

W8a oracle sampling hit the cap on every band and found only 1–2 optima.
The within-band spread of *P* is therefore unmeasured for W8a oracle; equal
saved scores do not establish a zero spread or uniqueness. Its saved sampled
*P* values 0.054688–0.472656 have 2–4 certified traps at resolution 2.229444.
The earlier W8a Hoeffding run did observe a spread on seed 1, as the table shows;
that observation also fails the grid resolution eligibility check.

The following are time-capped FEASIBLE incumbents, explicitly **non-optimal**.
Their κ and *P* are reported separately and never substituted for κ* or an
optimal-band basin prediction. Their two absolute errors are incumbent measurements.
Exact source rows are in the six linked CSVs above.

{incumbent_table}

### Section 6.3: seven completed timeout probes

{probe_table}

All seven probes returned UNKNOWN at the unchanged 1800 s cap, with no new
solution and unchanged certified bounds. Each used Formulation A, separate
c₀ = *k*_min and c₂ = *k*_max constraints, the saved incumbent hint, the original
seed and eight workers. None was skipped. Whether `LB_region` is exact on
these bands is unresolved. Original FEASIBLE records remain intact; UNKNOWN
does not prove optimality or infeasibility. See the exact
[JSON records](timeout-probe-v1.8.4.json) and [CSV](timeout-probe-v1.8.4.csv).

### Grid choices and gate evidence

The monotone grid rule chooses E8a 16, E8b 16, W8a 32, W8b 48 and R8a 16:
a size must pass along with every larger tested size. W8b's pass at 24 is
insufficient because 32 fails. These choices are recorded without starting E2
or Stage 2. Caps, seeds, thresholds and all completed count, sampling and probe
units are preserved. The [v1.8.4 gate](stage1-gate-v1.8.4.json) records the
six section 6.5 checks and the source digest recomputed from committed source.

Stage 1 shows that band resolution controls which minima remain visible: R8a
oracle recovers κ_true = 16, while E8a keeps κ* = 8 and reports *P* = `P0_res` = 1
against *P*₀ = 0.508, with zero certified traps and resolutions 2.717949/0.972242.
W8a oracle has 2–4 certified traps at resolution 2.229444, proving *P*₀ < 1
under coverage, but its *m* = 16 grid fails resolution, so no basin-prediction
conclusion is drawn. W8a oracle within-band spread remains unmeasured after
time-capped sampling of 1–2 optima. All seven probes are UNKNOWN; whether
`LB_region` is exact on those bands remains unresolved. No Stage 2 work was done.
'''


def run(check=False):
    record = persistence_record()
    encoded = json.dumps(record, indent=2, sort_keys=True, allow_nan=False)+'\n'
    path = ROOT/'docs/persistence-v1.8.4.json'
    stage1 = ROOT/'docs/STAGE1.md'
    section = render_section(record)
    if check:
        assert path.read_text(encoding='utf-8') == encoded, 'saved persistence table differs'
        assert stage1.read_text(encoding='utf-8').split(MARKER, 1)[1] == section.split(MARKER, 1)[1], 'section 6.4 differs from saved evidence'
    else:
        path.write_text(encoded, encoding='utf-8', newline='\n')
        before = stage1.read_text(encoding='utf-8').split(MARKER, 1)[0].rstrip()
        stage1.write_text(before+'\n\n'+section, encoding='utf-8', newline='\n')
    return dict(saved_fields=20, dataset_rows=120, documents_checked=check,
                persistence_sha256=sha256(path.read_bytes()).hexdigest())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    print(json.dumps(run(parser.parse_args().check)))
