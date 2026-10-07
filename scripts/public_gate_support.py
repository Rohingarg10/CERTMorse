"""Public reporting adaptations; every unblocked scientific assertion stays strict."""
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import re
import socket

ROOT = Path(__file__).resolve().parents[1]
POLICY = json.loads((ROOT/'docs/public-policy.json').read_text(encoding='utf-8'))
CHANGES = {r['path']:r for r in POLICY['approved_hash_changes']}
REMOVED = {r['path']:r for r in POLICY['approved_removed_files']}
MAP = POLICY['original_to_public_commits']


def public_path(value):
    value = str(value).replace('\\', '/')
    prefix = '<HOME>/Projects/CertMorse/'
    if value.startswith(prefix):
        return ROOT/value[len(prefix):]
    return Path(value)


def clean_text(value):
    home = str(Path.home())
    for spelling in sorted({home,home.replace('\\','/'),home.replace('\\','\\\\')},key=len,reverse=True):
        value = re.sub(re.escape(spelling),'<HOME>',value,flags=re.I)
    host = socket.gethostname()
    value = re.sub(r'(?i)\b'+re.escape(host)+r'\b','<HOST>',value)
    value = re.sub(r'(?i)pytest-of-'+re.escape(Path.home().name)+r'\b','pytest-of-<USER>',value)
    return value


def clean_report(value):
    if isinstance(value,str):
        return clean_text(value)
    if isinstance(value,list):
        return [clean_report(v) for v in value]
    if isinstance(value,dict):
        result={clean_text(k):clean_report(v) for k,v in value.items()}
        if 'command' in result and isinstance(result['command'],list):
            result['command'][0]='python'
        return result
    return value


def clean_file(path):
    data=path.read_bytes()
    text=data.decode('utf-8')
    cleaned=clean_text(text)
    if path.suffix=='.xml':
        for marker in ('HOME','HOST','USER'):
            cleaned=cleaned.replace('<'+marker+'>','&lt;'+marker+'&gt;')
    if cleaned!=text:
        path.write_bytes(cleaned.encode('utf-8'))


def verify_hash(path,expected):
    path=public_path(path)
    name=path.resolve().relative_to(ROOT).as_posix()
    if not path.exists():
        assert name in REMOVED and REMOVED[name]['original_sha256']==expected,('unexpected missing input',name)
        return dict(file=name,original_sha256=expected,status='BLOCKED_PRIVATE_FILE',reason='Historical input removed during public cleanup.')
    actual=sha256(path.read_bytes()).hexdigest()
    if actual!=expected:
        assert name in CHANGES,('unexpected hash mismatch',name,expected,actual)
        approved=CHANGES[name]
        assert approved['original_sha256']==expected and approved['public_sha256']==actual,('unapproved bytes',name)
        return dict(file=name,original_sha256=expected,public_sha256=actual,status='BLOCKED_APPROVED_REPLACEMENT',
                    reason='Historical hash retained; approved privacy/reference substitution changes public bytes.')
    assert actual==expected
    return dict(file=name,status='PASS',sha256=expected)


def verify_committed_source(gate):
    commit=gate.git('rev-parse','HEAD').decode().strip()
    digest,names=gate.committed_source_digest(commit)
    current=sorted(p.relative_to(ROOT).as_posix() for directory in ('certmorse','ttk_scripts')
                   for p in (ROOT/directory).rglob('*.py'))+['configs/instances.yaml']
    assert set(current)==set(names),'source file set differs from committed tree'
    assert digest==gate.source_digest(),'source bytes differ from committed tree'
    originals=['df07f35','7a3f16d','4f4a126']
    mapped=[]
    for prefix in originals:
        matches=[(old,new) for old,new in MAP.items() if old.startswith(prefix)]
        assert len(matches)==1
        mapped.append(matches[0][1])
        import subprocess
        subprocess.run(['git','merge-base','--is-ancestor',matches[0][1],commit],cwd=ROOT,check=True)
    pinned=gate.git('rev-parse','stage1-v1.8.3^{commit}').decode().strip()
    assert pinned==mapped[0],'mapped original tag moved'
    historical,_=gate.committed_source_digest(pinned)
    assert historical==gate.LEGACY_DIGEST,(historical,gate.LEGACY_DIGEST)
    return dict(commit=commit,source_digest=digest,committed_tree=True,source_files=len(names),
                mapped_source_commits=mapped,original_tag='stage1-v1.8.3',original_commit=pinned,
                original_source_digest=historical,private_history_checks=dict(status='BLOCKED_PRIVATE_HISTORY',
                original_refs=originals,reason='Pre-cleanup commit objects are intentionally absent from public history; equivalent mapped ancestry and source checks passed.'))


def verify_completion_hashes(gate):
    evidence=json.loads((ROOT/'docs/completion-evidence-v1.8.4.json').read_text(encoding='utf-8'))
    checks=[]
    assert len(evidence['units'])==evidence['unit_count']==179
    for name,unit in evidence['units'].items():
        folder=public_path(name)
        checks.append(verify_hash(folder/'config.json',unit['config_sha256']))
        checks.append(verify_hash(folder/'status.json',unit['status_sha256']))
        for output,digest in unit['status']['outputs'].items():
            checks.append(verify_hash(folder/output,digest))
        gate.check_unit(folder)
    for name,digest in evidence['report_sha256'].items():
        checks.append(verify_hash(name,digest))
    old=json.loads((ROOT/'docs/rescoring-v1.8.4.json').read_text(encoding='utf-8'))
    for name,digest in old['input_sha256'].items():
        checks.append(verify_hash(name,digest))
    assert len(old['input_sha256'])==176
    blocked=[r for r in checks if r['status']!='PASS']
    assert len(checks)==1717 and len(blocked)==3
    assert {r['file'] for r in blocked}=={'docs/completion-validation-v1.8.4.xml','docs/timeout-probe-v1.8.4.csv','docs/timeout-probe-v1.8.4.json'}
    return dict(units=179,hashes=len(checks),passed=len(checks)-len(blocked),legacy_inputs=176,
                status='BLOCKED_APPROVED_REPLACEMENT',blocked=blocked)


def verify_archive(archive,manifest):
    checks=[]
    for entry in manifest:
        checks.append(verify_hash(archive/entry['archived'],entry['sha256']))
        if entry['source'].startswith('results/'):
            checks.append(verify_hash(entry['source'],entry['sha256']))
    blocked=[r for r in checks if r['status']!='PASS']
    return dict(files=len(manifest),hash_checks=len(checks),passed=len(checks)-len(blocked),blocked=blocked,
                status='BLOCKED_PRIVATE_INPUTS' if blocked else 'PASS',
                all_archived_hashes_verified=not blocked,original_results_unchanged=not blocked)


def finish(report):
    blocked=[]
    for name in ('completion_hashes_before','archive'):
        blocked.extend(report['checks'][name].get('blocked',[]))
    blocked.append(report['checks']['committed_source']['private_history_checks'])
    report['blocked_checks']=blocked
    report['public_cleanup']=dict(affected_hash_inventory='docs/public-hash-checks.csv',potentially_affected=136,
        unchanged_after_declined_normalization=133,approved_report_hash_changes=3,old_hashes_modified=0,
        count_sampling_probe_units_rerun=0,identity_metadata_retained=True)
    report['checks']['original_gate_script']=dict(public_adaptation=True,unchanged_default_strict_checks=True,
        reason='Public mode records only exact registered privacy changes/removals as blocked; every other assertion is executed.')
    report['python_version']=platform.python_version()
    report['items']['1']['status']='BLOCKED_PRIVATE_INPUTS' if report['checks']['archive']['blocked'] else report['items']['1']['status']
    report['items']['2']['status']='BLOCKED_APPROVED_REPLACEMENT'
    report['items']['6']['status']='BLOCKED_PRIVATE_HISTORY'
    if report['status']=='PASS' and blocked:
        report['status']='BLOCKED'
        report['unblocked_checks_status']='PASS'

