"""Executable v1.8.4 gate; completed scientific units are read-only."""
import csv
from datetime import datetime,timezone
from hashlib import sha256
import json
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import yaml
from certmorse.complex import TorusComplex,lower_star_gradient
from certmorse.forman import witness,NegativeCycle,is_discrete_morse
from certmorse.metrics import basin_probability,critical_counts
from certmorse.instances import load_instance
from certmorse.provenance import source_digest
from certmorse.mip.regions import region_bound
from certmorse.resolution import RESOLUTION_INSTANCES,GRID_SIZES,INFORMATIVE_LIMIT
from scripts.agreement import passed
from scripts.repository_guard import RepositoryGuard
from scripts.test_scratch import allocate_scratch
from certmorse.completion_checks import completion_checks, probe_checks, check_unit
from certmorse.legacy_scores import LEGACY_DIGEST, verify_T38
from certmorse.scoring import score_arrays

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_GATE = os.environ.get('CERTMORSE_PUBLIC_GATE') == '1'
if PUBLIC_GATE:
    from scripts import public_gate_support
    Path = public_gate_support.public_path
    import certmorse.completion_checks as public_completion_checks
    public_completion_checks.Path = Path
    plugins = os.environ.get('PYTEST_PLUGINS', '')
    os.environ['PYTEST_PLUGINS'] = ','.join(filter(None, [plugins, 'scripts.public_gate_paths']))


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def committed_source_digest(ref):
    """Use precisely provenance.source_digest's file set, ordering and bytes."""
    names = git('ls-tree', '-r', '--name-only', ref).decode('utf-8').splitlines()
    names = [name for name in names if (name.startswith(('certmorse/', 'ttk_scripts/'))
                                        and name.endswith('.py')) or name == 'configs/instances.yaml']
    digest = sha256()
    for name in sorted(names, key=lambda name: ROOT/name):
        digest.update(name.encode('utf-8'))
        digest.update(b'\0'); digest.update(git('show', f'{ref}:{name}')); digest.update(b'\0')
    return digest.hexdigest(), names


def verify_committed_source():
    if PUBLIC_GATE:
        return public_gate_support.verify_committed_source(sys.modules[__name__])
    commit = git('rev-parse', 'HEAD').decode().strip()
    digest, names = committed_source_digest(commit)
    current = sorted(p.relative_to(ROOT).as_posix() for directory in ('certmorse', 'ttk_scripts')
                     for p in (ROOT/directory).rglob('*.py')) + ['configs/instances.yaml']
    assert set(current) == set(names), 'source file set differs from committed tree'
    assert digest == source_digest(), 'source bytes differ from committed tree'
    for short in ('df07f35', '7a3f16d', '4f4a126'):
        subprocess.run(['git', 'merge-base', '--is-ancestor', short, commit], cwd=ROOT, check=True)
    pinned = git('rev-parse', 'stage1-v1.8.3^{commit}').decode().strip()
    assert pinned == git('rev-parse', 'df07f35').decode().strip(), 'original tag moved'
    historical, _ = committed_source_digest(pinned)
    assert historical == LEGACY_DIGEST, (historical, LEGACY_DIGEST)
    return dict(commit=commit, source_digest=digest, committed_tree=True,
                source_files=len(names), section_8_commits=['df07f35', '7a3f16d', '4f4a126'],
                original_tag='stage1-v1.8.3', original_commit=pinned, original_source_digest=historical)


def verify_completion_hashes():
    if PUBLIC_GATE:
        return public_gate_support.verify_completion_hashes(sys.modules[__name__])
    evidence = json.loads(Path('docs/completion-evidence-v1.8.4.json').read_text(encoding='utf-8'))
    checked = 0
    def verify_hash(path, expected):
        nonlocal checked
        actual = sha256(Path(path).read_bytes()).hexdigest()
        assert actual == expected, (str(path), expected, actual)
        checked += 1
    assert len(evidence['units']) == evidence['unit_count'] == 179
    for name, unit in evidence['units'].items():
        folder = Path(name)
        verify_hash(folder/'config.json', unit['config_sha256'])
        verify_hash(folder/'status.json', unit['status_sha256'])
        for output, digest in unit['status']['outputs'].items():
            verify_hash(folder/output, digest)
        check_unit(folder)
    for name, digest in evidence['report_sha256'].items():
        verify_hash(name, digest)
    old = json.loads(Path('docs/rescoring-v1.8.4.json').read_text(encoding='utf-8'))
    for name, digest in old['input_sha256'].items():
        verify_hash(name, digest)
    assert len(old['input_sha256']) == 176
    return dict(units=179, hashes=checked, legacy_inputs=176, status='PASS')


def verify_rescoring():
    reproduced = verify_T38()
    report = json.loads(Path('docs/rescoring-v1.8.4.json').read_text(encoding='utf-8'))
    assert report['status'] == 'PASS' and report['T38'] and report['folders'] == 80
    cx = TorusComplex(16)
    for instance, mode in [('R8a', 'hoeffding'), ('E8a', 'hoeffding'), ('W8a', 'hoeffding'), ('R8a', 'oracle')]:
        target = Path(f'docs/stage1-{instance.lower()}-{mode}-rescored-v1.8.4.csv')
        with target.open(encoding='utf-8', newline='\n') as stream:
            rows = list(csv.DictReader(stream))
        assert len(rows) == 20 and {int(r['seed']) for r in rows} == set(range(20))
        for row in rows:
            path = Path(f'results/stage1-{instance.lower()}-v1.8.3-{mode}')/row['run_id']
            base = json.loads((path/'measurement.json').read_text(encoding='utf-8'))
            with np.load(path/'matching.npz') as data:
                arrays = {key: data[key] for key in data.files}
            scored = score_arrays(arrays, base)
            for key, value in scored.items():
                assert row[key] == ('' if value is None else str(value)), (target, row['seed'], key)
    return reproduced


def verify_documents():
    path = ROOT/'scripts/report-stage1-v1.8.4.py'
    spec = importlib.util.spec_from_file_location('report_stage1_v184', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    rendering = module.run(check=True)
    certificate = Path('docs/CERTIFICATE.md').read_text(encoding='utf-8')
    for required in ('v1.8.4', 'simplest landscape consistent with the', 'resolution, `P0_res`',
                     'never a certificate', 'Certified-trap definition', 'min_{v ∈ M} ℓ_v > min_v *u*_v + τ_min',
                     'persistence > 2*w*', '**Proposition.**', '**Proof.**', 'For (1)', 'For (2)', 'For (3)',
                     'P_possible_simplest', 'withdrawn as an ambiguity measure', 'unresolved'):
        assert required in certificate, ('CERTIFICATE.md missing', required)
    hashes = {}
    for name in ('docs/STAGE1.md', 'docs/CERTIFICATE.md', 'docs/persistence-v1.8.4.json'):
        raw = Path(name).read_bytes(); raw.decode('utf-8')
        assert b'\r' not in raw and not raw.startswith(b'\xef\xbb\xbf'), (name, 'not UTF-8/LF')
        hashes[name] = sha256(raw).hexdigest()
    return dict(status='PASS', sha256=hashes, rendering=rendering,
                renderer=str(path.relative_to(ROOT)), renderer_sha256=sha256(path.read_bytes()).hexdigest())


def run():
    repository_guard=RepositoryGuard(ROOT)
    repository_guard.activate()
    started=datetime.now(timezone.utc)
    output=Path('results/stage1-gate-v1.8.4')/started.strftime('%Y%m%dT%H%M%SZ')
    output.mkdir(parents=True,exist_ok=True)
    report=dict(specification='v1.8.4',amendments=['v1.8.1','v1.8.2','v1.8.3','v1.8.4'],
                started_at=started.isoformat(),source_digest=source_digest(),status='RUNNING',
                full_gate_ran=True,completed_scientific_units_rerun=0,steps=[],checks={},items={})
    destination=output/'gate.json'
    report['report_path']=str(destination)
    def save(): destination.write_text(json.dumps(public_gate_support.clean_report(report) if PUBLIC_GATE else report,indent=2),encoding='utf-8', newline='\n')
    def verify(path):
        assert yaml.safe_load((path/'config.yaml').read_text(encoding='utf8'))['source_digest']==LEGACY_DIGEST
        assert json.loads((path/'status.json').read_text(encoding='utf8'))['complete']
    def verify_matching(cx,x,y,lo,hi,count):
        a,b=cx.split_matching(y)
        assert is_discrete_morse(x,a,b,cx)[0]
        assert np.all((lo<=x)&(x<=hi))
        assert cx.nc-2*int(y.sum())==count
        assert not isinstance(witness(a,b,lo,hi,cx),NegativeCycle)
    save()
    # Full tests create isolated test fixtures (including T37's interruption
    # controls). No Stage 1 count/sampling/probe driver is called by this gate.
    test_scratch=allocate_scratch()
    commands=[('tests',[sys.executable,'-m','pytest','-q','-x','--basetemp='+str(test_scratch),
                        '--junitxml='+str(output/'tests.xml')])]
    item = 6
    try:
        report['checks']['committed_source']=verify_committed_source()
        report['items']['6']=dict(status='PASS', **report['checks']['committed_source']);save()
        item = 2
        report['checks']['completion_hashes_before']=verify_completion_hashes();save()
        report['checks']['rescoring']=verify_rescoring()
        report['items']['2']=dict(status='PASS', primary_folders=80,
                                  optimal_bands=report['checks']['rescoring']['optimal_bands'],
                                  sampled_optima=report['checks']['rescoring']['sampled_optima'],
                                  exact_T38=True);save()
        item = 3
        report['checks']['oracle_completion']=completion_checks()
        completion = report['checks']['oracle_completion']['instances']
        assert completion['E8a']['optimal'] == 20 and completion['W8a']['optimal'] == 10
        assert sum(r['sampled_optima'] for r in completion.values()) == 411
        report['items']['3']=dict(status='PASS', new_counts=40, oracle_bands=60,
                                  sampling_runs=30, sampled_optima=411, instances=completion);save()
        item = 4
        report['checks']['probes']=probe_checks()
        assert report['checks']['probes']['outcomes'] == {'UNKNOWN': 7}
        report['items']['4']=dict(report['checks']['probes']);save()
        item = 5
        report['checks']['documents']=verify_documents()
        report['items']['5']=dict(status='PASS', sha256=report['checks']['documents']['sha256']);save()
        item = 1
        t34=json.loads(Path('docs/T34-v1.8.3.json').read_text(encoding='utf8'))
        assert t34['source_digest']==LEGACY_DIGEST
        assert datetime.fromisoformat(t34['bands']['hoeffding']['completed_at'])<started
        report['checks']['T34_hoeffding_before_gate']=t34['bands']['hoeffding'];save()
        for name,command in commands:
            print(f'Running {name}',flush=True);start=time.perf_counter()
            log=output/(name+'.log')
            with log.open('w',encoding='utf-8', newline='\n') as stream:
                result=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT)
            report['steps'].append(dict(name=name,command=command,exit_code=result.returncode,
                                       wall_s=time.perf_counter()-start,log=str(log)));save()
            if result.returncode: raise AssertionError(f'{name} failed; see {log}')
            if name=='tests':
                cases=ET.parse(output/'tests.xml').findall('.//testcase')
                assert cases and not any(c.find('skipped') is not None for c in cases),'required integrations must not be skipped'
                report['checks']['tests']=dict(passed=len(cases),skipped=0);save()
        cases=ET.parse(output/'tests.xml').findall('.//testcase')
        assert cases and not any(c.find('skipped') is not None for c in cases),'required integrations must not be skipped'
        assert not any(c.find('failure') is not None or c.find('error') is not None for c in cases)
        report['checks']['tests']=dict(passed=len(cases),skipped=0)
        test_ids = set()
        import re
        for case in cases:
            test_ids.update(int(n) for n in re.findall(r'T(\d+)', case.get('name', '')))
        # v1.6 section 2a places T12 (optimizer measurement), T13
        # (allocation), and T18 (forecast calibration) in Stage 2.
        # Preserve that scope and run every Stage 1 test, with no skips.
        required_ids = set(range(1,40))-{12,13,18}
        assert required_ids <= test_ids, ('missing tests', sorted(required_ids-test_ids))
        report['checks']['tests']['test_ids'] = sorted(test_ids)
        report['checks']['tests']['stage2_ids'] = [12,13,18]
        report['checks']['tests']['scope'] = 'Stage 1, v1.6 section 2a; no Stage 2 work'
        for test_id in (36,37,38,39):
            selected = [c for c in cases if f'T{test_id}' in c.get('name', '')]
            assert selected and all(c.find('failure') is None and c.find('error') is None and c.find('skipped') is None for c in selected)
            report['checks'][f'T{test_id}'] = dict(passed=len(selected), skipped=0)
        for phase in ('solve', 'file-write'):
            evidence = json.loads((test_scratch/f'reports/T37-{phase}-v1.8.4.json').read_text(encoding='utf-8'))
            assert evidence['status']=='PASS' and evidence['first_band_preserved'] and evidence['second_band_restarted']
            assert evidence['deterministic_units_byte_identical'] and evidence['solver_status_bounds_and_witnesses_verified']
            report['checks'][f'T37_{phase}'] = evidence
        guard_report=json.loads((test_scratch/'reports/repository-guard.json').read_text(encoding='utf-8'))
        assert guard_report['status']=='PASS' and guard_report['tracked_hashes_unchanged']
        assert guard_report['before_status']==guard_report['after_status']
        report['checks']['test_repository_guard']=guard_report
        rows=json.loads(Path('docs/agreement-v1.8.3.json').read_text(encoding='utf8'))
        assert {(r['m'],r['seed']) for r in rows}=={(m,s) for m in [3,4,8] for s in range(20 if m==8 else 50)}
        assert len(rows)==120 and all(passed(r) and passed(dict(methods=r['controls'])) and r['rows_preserve_optimum'] for r in rows)
        for row in rows:
            cx=TorusComplex(row['m'])
            for family in ('methods','controls'):
                for record in row[family].values():
                    path=Path(record['run_path']);verify(path)
                    with np.load(path/'solution.npz') as data:
                        verify_matching(cx,data['x'],data['y'],data['lo'],data['hi'],record['kappa_opt'])
        report['checks']['agreement']=dict(bands=120,optimal_solves=720,exact_witnesses_verified=720,
                                          valid_rows_preserve_all_optima=True)
        t34=json.loads(Path('docs/T34-v1.8.3.json').read_text(encoding='utf8'))
        assert set(t34['bands'])=={'hoeffding','m32-0','m32-1','m32-2'}
        for pilot in t34['bands'].values():
            for record in pilot['methods'].values():
                path=Path(record['run_path']);verify(path)
                with np.load(path/'solution.npz') as data:
                    m=yaml.safe_load((path/'config.yaml').read_text(encoding='utf8'))['grid_m']
                    verify_matching(TorusComplex(m),data['x'],data['y'],data['lo'],data['hi'],record['kappa_incumbent'])
        report['checks']['T34']=t34
        resolution=json.loads(Path('docs/resolution-v1.8.3.json').read_text(encoding='utf8'))
        assert resolution['source_digest']==LEGACY_DIGEST
        assert {(r['instance'],r['grid_m']) for r in resolution['rows']}=={(i,m) for i in RESOLUTION_INSTANCES for m in GRID_SIZES}
        assert len(resolution['rows'])==20
        for r in resolution['rows']:
            verify(Path(r['run_path']))
            assert r['resolution_adequate']==(r['grid_global']==r['continuous_global'])
            assert r['RQ2_informative']==(r['resolution_adequate'] and r['P0_grid']<=INFORMATIVE_LIMIT)
        report['checks']['resolution']=resolution
        summaries={};failures=[]
        for instance,mode in [('R8a','hoeffding'),('E8a','hoeffding'),('W8a','hoeffding'),('R8a','oracle')]:
            with Path(f'docs/stage1-{instance.lower()}-v1.8.3-{mode}.csv').open(newline='') as stream:
                measurements=list(csv.DictReader(stream))
            assert len(measurements)==20 and {int(r['seed']) for r in measurements}==set(range(20))
            cx=TorusComplex(16);inst=load_instance(instance);ranges=[];sample_total=0
            for row in measurements:
                path=Path(f'results/stage1-{instance.lower()}-v1.8.3-{mode}')/row['run_id'];verify(path)
                with np.load(path/'matching.npz') as data:
                    field,offset=np.loadtxt(path/'simplified.csv',delimiter=',',skiprows=1).T
                    assert len(np.unique(offset))==cx.nv
                    order=np.lexsort((offset,field));rank=np.empty(cx.nv,dtype=np.int64);rank[order]=np.arange(cx.nv)
                    wa,wb=lower_star_gradient(rank,cx)
                    warm=witness(wa,wb,data['cell_lo'],data['cell_hi'],cx)
                    accepted=not isinstance(warm,NegativeCycle)
                    assert accepted==(row['ttk_warm_status']=='accepted')
                    warm_count=cx.nc-2*int(wa.sum()+wb.sum())
                    assert (int(row['ttk_warm_count'])==warm_count) if accepted else not row['ttk_warm_count']
                    midpoint=(data['cell_lo'][:cx.nv]+data['cell_hi'][:cx.nv])/2
                    ma,mb=lower_star_gradient(midpoint,cx)
                    expected='ttk_simplified' if accepted and wa.sum()+wb.sum()>=ma.sum()+mb.sum() else 'midpoint'
                    assert row['warm_start_used']==expected
                    assert (row['UB_witness_justified']=='True')==(accepted and warm_count<=int(row['UB_pers']))
                    verify_matching(cx,data['x'],data['y'],data['cell_lo'],data['cell_hi'],int(row['kappa_incumbent']))
                    counts=critical_counts(data['y'],cx)
                    assert counts==tuple(int(row[k]) for k in ('c0','c1','c2'))
                    regions=region_bound(data['cell_lo'],data['cell_hi'],cx)
                    assert regions.LB_region==int(row['LB_region'])<=int(row['kappa_incumbent'])
                    assert int(row['kappa_cert'])==max(int(row['kappa_lb']),regions.LB_region)
                    assert int(row['kappa_cert'])<=int(row['kappa_incumbent'])
                    ta,tb=lower_star_gradient(data['truth'],cx)
                    transfer=not isinstance(witness(ta,tb,data['cell_lo'],data['cell_hi'],cx),NegativeCycle)
                    covered=bool(np.all((data['lower']<=data['truth'])&(data['truth']<=data['upper'])))
                    assert (row['transfer_claim']=='True')==(covered and transfer)
                    assert (row['coverage']=='True')==covered and (row['transfer_ok']=='True')==transfer
                    if covered and transfer: assert int(row['kappa_cert'])<=cx.nc-2*int(ta.sum()+tb.sum())
                    if row['status']=='OPTIMAL':
                        assert row['kappa_opt'] and int(row['kappa_opt'])==int(row['kappa_incumbent'])
                        P,possible=basin_probability(data['y'],data['mean'],inst.W,cx,data['lower'],data['upper'])
                        assert P==float(row['P_first']) and possible==float(row['P_possible'])
                    else:
                        assert not row['kappa_opt'] and not row['P_first'] and not row['P_possible']
                    optima=data['optima'];assert len(optima)==int(row['n_opt_found'])
                    assert len(np.unique(optima[:,:len(cx.pairs_ve)],axis=0))==len(optima)
                    values=[]
                    for y in optima:
                        assert row['status']=='OPTIMAL'
                        aa,bb=cx.split_matching(y);x=witness(aa,bb,data['cell_lo'],data['cell_hi'],cx)
                        assert not isinstance(x,NegativeCycle)
                        verify_matching(cx,x,y,data['cell_lo'],data['cell_hi'],int(row['kappa_opt']))
                        values.append(basin_probability(y,data['mean'],inst.W,cx,data['lower'],data['upper'])[0])
                    if values:
                        np.testing.assert_allclose([min(values),np.median(values),max(values)],
                                                   [float(row[k]) for k in ('P_lo','P_med','P_hi')],rtol=0,atol=0)
                        ranges.append(max(values)-min(values));sample_total+=len(values)
                    if instance=='R8a' and row['status']=='OPTIMAL': assert P==1 and all(v==1 for v in values)
                    assert row['basin_conclusion_eligible']==row['resolution_adequate']
                    assert row['bound_violation']==str(int(row['kappa_incumbent'])<int(row['LB_mand']))
            optimal=[r for r in measurements if r['status']=='OPTIMAL']
            sampled=[r for r in measurements if int(r['n_opt_found'])]
            summary=dict(bands=20,optimal=len(optimal),timeouts=sum(r['status']!='OPTIMAL' for r in measurements),
                count_bound_range=[min(int(r['kappa_lb']) for r in measurements),max(int(r['kappa_lb']) for r in measurements)],
                incumbent_range=[min(int(r['kappa_incumbent']) for r in measurements),max(int(r['kappa_incumbent']) for r in measurements)],
                kappa_equals_region=sum(int(r['kappa_opt'])==int(r['LB_region']) for r in optimal),optimal_denominator=len(optimal),
                region_equals_mandatory=sum(int(r['LB_region'])==int(r['LB_mand']) for r in measurements),
                mandatory_violations=sum(r['bound_violation']=='True' for r in measurements),
                multiplicity_bands=len(ranges),sampled_optima=sample_total,
                sample_count_range=None if not sampled else [min(int(r['n_opt_found']) for r in sampled),max(int(r['n_opt_found']) for r in sampled)],
                sampling_status_counts={status:sum(r['sampling_status']==status for r in sampled)
                                        for status in sorted({r['sampling_status'] for r in sampled})},
                observed_spread_range=None if not ranges else [min(ranges),max(ranges)],
                bands_with_spread=sum(v>0 for v in ranges),resolution_adequate=measurements[0]['resolution_adequate']=='True',
                basin_conclusion_eligible=measurements[0]['basin_conclusion_eligible']=='True',
                P0_grid=float(measurements[0]['P0_grid']),P0_cont=float(measurements[0]['P0_cont']),
                solver_wall_range=[min(float(r['wall_s']) for r in measurements),max(float(r['wall_s']) for r in measurements)])
            summaries[instance+'-'+mode]=summary
            if mode=='hoeffding' and len(ranges)!=10: failures.append(f'{instance}: {len(ranges)}/10 requested multiplicity bands available')
        report['checks']['measurements']=summaries
        study=json.loads(Path('docs/coverage-study-v1.8.3.json').read_text(encoding='utf8'))
        assert study['total']==2000 and study['seed_start']==10000 and study['seed_end']==11999
        assert not study['modes']['oracle']['simultaneous_guarantee'] and study['modes']['hoeffding']['simultaneous_guarantee']
        assert study['modes']['oracle']['covered']==1896 and study['modes']['hoeffding']['covered']==2000
        report['checks']['coverage']=study
        archive=Path('docs/archive/v1.7');manifest=json.loads((archive/'manifest.json').read_text(encoding='utf8'))
        if PUBLIC_GATE:
            report['checks']['archive']=public_gate_support.verify_archive(archive,manifest)
        else:
            for entry in manifest:
                assert sha256((archive/entry['archived']).read_bytes()).hexdigest()==entry['sha256']
                if entry['source'].startswith('results/'):
                    assert sha256(Path(entry['source']).read_bytes()).hexdigest()==entry['sha256']
            report['checks']['archive']=dict(files=len(manifest),all_archived_hashes_verified=True,original_results_unchanged=True)
        report['checks']['completion_hashes_after']=verify_completion_hashes()
        assert report['checks']['completion_hashes_after']==report['checks']['completion_hashes_before']
        assert verify_committed_source()==report['checks']['committed_source'], 'committed source changed during gate'
        assert verify_documents()==report['checks']['documents'], 'documents changed during gate'
        assert source_digest()==report['source_digest'],'implementation changed during gate'
        report['checks']['repository_guard']=repository_guard.verify()
        report['items']['1']=dict(status='FAIL' if failures else 'PASS', **report['checks']['tests'])
        assert set(report['items'])==set('123456')
        report['failed_requirements']=failures;report['status']='FAIL' if failures else 'PASS'
        if PUBLIC_GATE:
            public_gate_support.finish(report)
            for step in report['steps']:
                public_gate_support.clean_file(Path(step['log']))
            public_gate_support.clean_file(output/'tests.xml')
        report['completed_at']=datetime.now(timezone.utc).isoformat();save();print(json.dumps(public_gate_support.clean_report(report) if PUBLIC_GATE else report),flush=True)
    except Exception as error:
        report['status']='FAIL';report['error']=str(error);report['failing_item']=item
        report['items'][str(item)]=dict(status='FAIL',error=str(error))
        xml = output/'tests.xml'
        if xml.exists():
            cases = ET.parse(xml).findall('.//testcase')
            report['test_counts']=dict(total=len(cases), failures=sum(c.find('failure') is not None or c.find('error') is not None for c in cases),
                                       skipped=sum(c.find('skipped') is not None for c in cases))
        report['completed_at']=datetime.now(timezone.utc).isoformat();save();raise
    finally:
        repository_guard.active=False
    return report


if __name__=='__main__':
    assert os.environ.get('CERTMORSE_PVPYTHON') and os.environ.get('CERTMORSE_TSFM_PYTHON'),'run scripts/stage1-gate.ps1'
    result=run()
    if result['status'] not in (('PASS','BLOCKED') if PUBLIC_GATE else ('PASS',)): sys.exit(1)
