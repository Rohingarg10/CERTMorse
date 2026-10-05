"""Render the evaluated v1.8 gate and certificate; never infer a gate pass."""
import json
from datetime import datetime,timezone
from hashlib import sha256
from pathlib import Path
import sys
import time


def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+
                      ['| '+' | '.join(map(str,row))+' |' for row in rows])


def run():
    started=time.perf_counter()
    gate=json.loads(Path('docs/stage1-gate.json').read_text(encoding='utf8'))
    assert gate['status'] in ('PASS','FAIL'),'render final documents only after gate evaluation'
    checks=gate['checks'];measurements=checks.get('measurements',{})
    t34=json.loads(Path('docs/T34-v1.8.3.json').read_text(encoding='utf8'))
    resolution=json.loads(Path('docs/resolution-v1.8.3.json').read_text(encoding='utf8'))
    t31=json.loads(Path('docs/T31-v1.8.3.json').read_text(encoding='utf8'))
    test=checks.get('tests',{})
    intro=f'''# Stage 1 evidence for v1.8, amended through v1.8.3

**Gate status: {gate['status']}.** Evaluated by `scripts/stage1-gate.py`; the executable
[gate report](stage1-gate.json) contains commands, exit codes, source digest,
logs and independent artifact checks. Branch: `v1.8`. No Stage 2 module or experiment was started.
The source digest is `{gate['source_digest']}`.

The gate recorded {test.get('passed','not completed')} passing tests and
{test.get('skipped','not evaluated')} skipped tests.{(' ' + gate['error']) if gate.get('error') else ''}
Failed requirements: {gate.get('failed_requirements',[])}.

## Independent review and preserved failures

Before implementation, every requested v1.8 §3 finding reproduced:
all 200 archived optima gave depth P=1 (old critical-vertex scoring reached
0.27734375); all 12 ideal fields passed beta pi/2 and their listed gamma
symmetries; R8a had 112 old-grid adjacent ties and the quarter grid had zero
ties on all twelve ideal instances at m=16 and 32; all 20 archived R8a oracle
bands gave LB_region=32 (eight minimum and eight maximum regions).
[Independent reproduction](review-reproduction-v1.8.json).
The explicit symmetry lists contain eight symmetric and four nonsymmetric
instances; v1.8's prose count of nine and three is inconsistent with those lists.

The v1.7 archive contains 6,872 byte-preserved files and its SHA-256 manifest.
[Archive](archive/v1.7/README.md). The gate checks the archive hashes and original
result-file hashes. New measurements use separate v1.8.3 result directories.

The original T29 run stopped with **2 passed, 1 failed**: R8a amplitude damping
breaks beta pi/2 with error **0.014559172029865675** (point seed 29, circuit seed 7).
[Failing T29 XML](v1.8-amendment-preflight.xml),
[original gate](v1.8-preflight-gate.json).
V1.8.1 replaces that assertion: beta pi for every channel, pi/2 for all except
amplitude damping, whose R8a half-period failure is a required negative control.
Measured per-channel gamma metadata accompanies the saved fields.

The original T32 run stopped with **1 failed**: on the proven kappa=16 narrow-band
R8a optimum, P=1 but the old P_possible=0.5234375.
[Counterexample](t32-counterexample-v1.8.1.json),
[failing XML](v1.8.1-basin-preflight.xml),
[preserved gate](v1.8.1-preflight-gate.json).
V1.8.2 adds the same 0.02W tolerance to P_possible; the preserved counterexample
now gives P=P_possible=1. The old definition remains a named test control.
The scorer asserts that the depth field lies in the reported band.

The first full-gate attempt was interrupted by laptop standby and hibernation.
E8a seed 9 exhausted its elapsed presolve budget with no initialized objective
bound; the numerical guard rejected that response. The failed gate and all
affected evidence were archived before recovery. R8a seed 4 and E8a seeds 5-9
were replayed because their execution intervals overlapped recorded standby;
all other completed runs, including the two R8a timeouts, were retained.
Recovery uses the original seeds and 600 s count / 300 s sampling caps and
a temporary Windows wake request, released when the launcher finished.
No scientific rule or threshold changed.
[public method](METHOD.md), [recovery manifest](stage1-sleep-recovery.json).

## Amendment checks

Synthetic fields retain the v1.6 beta-pi grid and known answers. QAOA uses
the single quarter-offset `grid_point`/`grid_coords` conversion, tested by T35.
Strict extrema use the six triangulation neighbours. Fixed-scale kappa_zero
uses S0=10^6 and half-width 500/S0 with the unchanged 14-unit margin.

T31 solved {t31['optimal_bands']} random m=4 bands to OPTIMAL, verified the
disjoint regions and critical cells, and found LB_region=kappa* on
{t31['equal']}/{t31['optimal_bands']} ({t31['equality_rate']:.0%}).
T33 compares the same 120 bands, three methods, with and without rows (720 solves).
The gate independently rechecks the saved witnesses, bounds and counts.

## T34: archived bands, measured before the full gate

Both arms use identical archived integer bands, hints, seeds, eight threads
and the original caps (600 s Hoeffding; 60 s m=32). Improvement is not asserted.
[T34 measurements](T34-v1.8.3.json).
'''
    bound_rows=[]
    for label,pilot in t34['bands'].items():
        for arm,r in pilot['methods'].items():
            bound_rows.append([label,arm,r['status'],r['kappa_lb'],r['kappa_incumbent'],r['kappa_opt'],f"{r['wall_s']:.2f}"])
    intro+= '\n'+table(['Band','Rows','Status','Count bound','Incumbent','Optimum','Seconds'],bound_rows)+'\n'
    h=t34['bands']['hoeffding']['methods'];before=h['no-rows'];after=h['rows']
    intro+=f'''
For the archived Hoeffding pilot the count bound changed from {before['kappa_lb']}
to {after['kappa_lb']}, the incumbent from {before['kappa_incumbent']} to
{after['kappa_incumbent']}, and status from {before['status']} to {after['status']}.
LB_region in the row arm is {after['LB_region']}. The archived v1.7 run itself
was FEASIBLE at 600 s with count bound 4 and incumbent 20. The paired current
no-row arm is the appropriate control for isolating the rows.

## Full-gate measurements

'''
    rows=[]
    for label,r in measurements.items():
        rows.append([label,r['optimal'],r['timeouts'],f"{r['kappa_equals_region']}/{r['optimal_denominator']}",
                     f"{r['region_equals_mandatory']}/20",r['multiplicity_bands'],r['sampled_optima'],r['observed_spread_range']])
    intro+=table(['Dataset','Optimal','Timeouts','Optimum=region','Region=mandatory','Sampled bands','Optima','Observed P spread'],rows)+'\n'
    if not measurements:
        intro+='\nThe measurement phase did not complete; E8a and W8a spread and new-grid timeout rates are unmeasured in this gate.\n'
    for name in ('E8a','W8a'):
        r=measurements.get(name+'-hoeffding')
        if r:
            intro+=f"\n{name}: {r['bands_with_spread']}/{r['multiplicity_bands']} sampled bands show nonzero P spread; range {r['observed_spread_range']}. "
            intro+=('Resolution passes; this is an eligible basin measurement.\n' if r['resolution_adequate'] else
                    'Resolution fails at m=16; these raw solver measurements are excluded from basin-prediction conclusions.\n')
    for label,r in measurements.items():
        if r['multiplicity_bands']:
            intro+=f"\n{label}: sampled count range {r['sample_count_range']}, statuses {r['sampling_status_counts']}.\n"
    intro+='\nSampling uses the fixed count, random secondary vertex-edge weights, signed\nno-good cuts and first-feasible solves; cap 20 optima including the first,\n300 s per band. Ranges are observed and medians procedural, not uniform samples.\n\nThe ten sampling bands are the first ten OPTIMAL bands in seed order. If a\nprimary sampling slot times out in count optimization, supplemental sampling\nuses an already proven subsequent band among the same twenty; its separate\nconfiguration and logs are linked by `multiplicity_run_path`. No primary count\nsolve is repeated, and no cap or threshold is changed.\n\n'
    if 'multiplicity_provenance' in checks:
        intro+='Independent sampling verification passed for all 30 selected bands,\nincluding the six supplemental bands: unchanged source and driver hashes,\nseed selection, fixed caps, primary/sidecar arrays and every saved basin\nscore were checked. [Verification](multiplicity-verification-v1.8.3.json).\n\n'
    intro+='## Resolution check\n\n'
    rrows=[[r['instance'],r['grid_m'],r['resolution_adequate'],f"{r['worst_grid_depth_error']:.6f}",
            f"{r['P0_grid']:.6f}",f"{r['P0_cont']:.6f}",r['RQ2_informative']] for r in resolution['rows']]
    intro+=table(['Instance','m','Adequate','Worst depth error','P0 grid','P0 continuous','Informative'],rrows)+'\n'
    intro+=f'''
[Resolution artifacts](resolution-v1.8.3.json). Nelder–Mead uses xatol=1e-9,
fatol=1e-12 and stops when its iterate leaves the starting basin's half-open
nearest-vertex grid cells (the equal vertex-area convention of D11).
The measured smallest passing sizes are {resolution['smallest_passing_grid']}.
These follow the amendment's classification rule; its forecast of m=32 for
E8a/E8b/R8a and m=48 for W8b is not the measured minimum. Adequacy is not
monotonic: W8b passes m=24 but fails m=32.
The p=2 fallback is {resolution['p2_fallback']}; informative E8a/E8b pairs are
available. No spread or agreement measurement is used as a switching criterion.
'''
    coverage=checks.get('coverage')
    if coverage:
        intro+='\n## Paired coverage\n\n'
        intro+=table(['Band','Covered / 2000','Coverage','Wilson 95%','Guarantee'],
                    [[mode,f"{r['covered']}/2000",r['coverage'],r['wilson95'],r['simultaneous_guarantee']]
                     for mode,r in coverage['modes'].items()])+'\n\nSeeds 10000–11999, paired shots on the new R8a grid. Gaussian coverage is\nmeasured and approximate; Hoeffding has the bounded-shot union-bound guarantee.\n[Coverage study](coverage-study-v1.8.3.json).\n'
    Path('docs/STAGE1.md').write_text(intro,encoding='utf8')
    archived=Path('docs/archive/v1.7/CERTIFICATE.md').read_text(encoding='utf8')
    transfer=archived.split('## Transfer theorem and complete proof\n',1)[1].split('The condition is sufficient',1)[0]
    numerical=archived.split('## Equivalent numerical representation\n',1)[1]
    cert=f'''# Certificate semantics: v1.8 amended through v1.8.3

Stage 1 gate: **{gate['status']}**. [Gate report](stage1-gate.json) and
[measurements](STAGE1.md) delimit the evidence. No Stage 2 experiment was run.

## Integer-model certificate

The model maximizes incidence matches; each cell appears in at most one pair.
Matched cofaces have value at most their partner face; unmatched incidences
increase by at least one. Integer potentials lie in the original cell band.
Thus no closed V-path exists. Every accepted matching is independently checked
with exact integer Bellman–Ford and the discrete-Morse validator.
For a CP-SAT upper bound B on matches, kappa_lb=6m²−2floor(B), including at
timeout. Only OPTIMAL establishes kappa*. HiGHS bounds remain numerical
benchmarks. This relies on CP-SAT's integer reasoning and reported bound.
Formulation B's relaxation bound remains valid before its matching is accepted;
both V-cycles and signed band-infeasibility cycles must be separated.

## Region bound and valid rows: proof

For vertex a, C(a) is its component in {{v:lo_v<=hi_a}} on the six-neighbour
graph. Every boundary vertex w has lo_w>hi_a. The smallest-valued vertex v*
inside C(a) has x_v*<=x_a<=hi_a. If v* were matched to an edge, that edge's
other vertex would have strictly smaller value (the other incidence is
unmatched). Such a vertex exists neither inside C(a), by minimality, nor on
its boundary, by the bound. Hence C(a) contains a critical vertex.

D(b) is triangle b's component in {{t:hi_t>=lo_b}} in the edge-sharing dual
graph. A matched triangle t paired to edge e has an unmatched neighbouring
triangle t' across e, with x_t'>x_e>=x_t. The largest-valued triangle in D(b)
has value at least x_b>=lo_b; every boundary triangle has value below lo_b.
It therefore cannot be matched and D(b) contains a critical triangle.

Threshold components are laminar: when two overlap, the lower-threshold
component is contained in the higher-threshold component (reverse thresholds
for maxima). Inclusion-minimal members are consequently pairwise disjoint.
Each requires its own critical cell. With k_min and k_max minimal regions,
c0>=k_min and c2>=k_max. Since c0−c1+c2=0 on the torus,
kappa=2(c0+c2)>=2(k_min+k_max)=LB_region.

Region rows encode exactly one or more critical cells per disjoint minimal
region. Morse rows c0>=1,c1>=2,c2>=1 hold for the torus. Substitution of the
matching expressions into Euler cancels every y term and leaves
|V|−|E|+|T|=m²−3m²+2m²=0; the Euler row is identically valid even in the
relaxation. Adding these rows removes no feasible integer matching. Summing
the region rows and Euler gives the same LB_region in the relaxation.
T33 tests preservation for all 120 bands and three methods.

The certified count is max(CP-SAT kappa_lb,LB_region). This applies first to
the integer model; the following coverage/transfer hypotheses connect it to
the true field. LB_mand and persistence counts remain cross-checks.
Together the two bounds give kappa_cert<=kappa*<=kappa_true under those hypotheses.

## Transfer theorem and complete proof

{transfer}
The separation condition is sufficient, not necessary. Simulation records
coverage and direct exact transfer separately, and claims transfer only when
both hold. Ties are counted with |delta F|<1e-12. kappa_true is reported only
without adjacent ties, with the six-neighbour extrema identity; otherwise
kappa_zero is the OPTIMAL fixed-S0=10^6, half-width 500/S0 diagnostic.

## Symmetry, grid and scope

Beta has period pi for all channels and pi/2 for a,b,d,d0,e. Amplitude damping
c breaks pi/2, established by the preserved T29 failure. Its domain is
[0,pi); the others use [0,pi/2). Gamma always has period 2pi. Actual gamma
shift or shift/reflection symmetry is measured at 100 random points, tolerance
1e-12, for each instance/channel; ideal YAML values are reference data only.
Counts use the full applicable torus, with per-copy counts only if divisible.
Conjugation holds continuously for a,b,c and is tested off grid.
Quarter-offset conversions use grid_point/grid_coords, including VTK and
independent references. Synthetic tests retain the original beta-pi grid.

## Basin predictions and resolution

For each matching, basin depth is the minimum observed field value in the
basin, independent of arbitrary witness values. P counts basin areas whose
depth is within tau=0.02W of the smallest depth. P_possible counts basins with
minimum reported lower endpoint <= minimum reported upper endpoint +tau.
The observed depth field G must satisfy lower<=G<=upper at every vertex.
For a basin counted by P, min_B lower<=min_B G<=min G+tau<=min upper+tau:
evaluate G at a vertex attaining min upper for the final inequality.
Therefore P<=P_possible. Both use the reported unscaled band before margins.
The preserved old T32 failure demonstrates why the same tolerance is needed.

The certificate is a grid count statement; it certifies neither basin area nor
continuum minima. The simulation-only resolution test refines basin minima by
Nelder–Mead and compares global classifications. W8a m=16 fails and is excluded
from basin conclusions. RQ2-informative means P0_grid<=0.95 and resolution
adequate. P differences and multiplicity ranges never determine fallback.
Sampling starts only from OPTIMAL; medians are procedural and ranges observed
unless enumeration is exhausted.

## Statistical and persistence contracts

Hoeffding uses independent bounded shot outcomes and Bonferroni over all grid
vertices. Gaussian modes are approximations. The paired 2000-seed study is
recorded in STAGE1.md. The retained adaptive contract covers vertices and every
predeclared deterministic sample size, including data-dependent stopping;
no adaptive Stage 2 experiment is undertaken here.
Persistence uses the closure filtration phi(c)=min over cofaces x(rho),
coefficients Z/2, and top-dimensional persistence, retaining essential
dimensions 0,1,1,2. Both bottleneck sides use that filtration and their scale.
TTK essential endpoints are decoded with IsFinite.

## What the MIP adds beyond the region bound

'''
    cert+=table(['Dataset','kappa*=LB_region / optimal','LB_region=LB_mand / 20'],
                [[label,f"{r['kappa_equals_region']}/{r['optimal_denominator']}",f"{r['region_equals_mandatory']}/20"]
                 for label,r in measurements.items()])+'\n'
    cert+=f'\nRandom-band T31 equality is {t31["equal"]}/{t31["optimal_bands"]}; the count solve can add information beyond the region bound.\n\n## Equivalent numerical representation and TTK starts\n\n'+numerical
    Path('docs/CERTIFICATE.md').write_text(cert,encoding='utf8')
    hashes={str(path):sha256(path.read_bytes()).hexdigest() for path in
            (Path('docs/STAGE1.md'),Path('docs/CERTIFICATE.md'))}
    gate['checks']['documents']=dict(sha256=hashes,renderer='scripts/report-stage1.py',
                                    renderer_sha256=sha256(Path(__file__).read_bytes()).hexdigest())
    directory=Path(gate['steps'][0]['log']).parent if gate['steps'] else Path('results/stage1-gate-v1.8.3/document-report')
    directory.mkdir(parents=True,exist_ok=True);log=directory/'documents.log'
    log.write_text(json.dumps(gate['checks']['documents'],indent=2),encoding='utf8')
    gate['steps'].append(dict(name='documents',command=[sys.executable,'scripts/report-stage1.py'],exit_code=0,
                              wall_s=time.perf_counter()-started,log=str(log)))
    gate['completed_at']=datetime.now(timezone.utc).isoformat()
    Path('docs/stage1-gate.json').write_text(json.dumps(gate,indent=2),encoding='utf8')


if __name__=='__main__': run()
