"""Explicitly publish a validated scratch gate report; the gate never does this."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def record(source):
    source = (ROOT/source).resolve()
    if not source.is_relative_to((ROOT/'results').resolve()):
        raise ValueError('Select a gate report from ignored results scratch output')
    report = json.loads(source.read_text(encoding='utf-8'))
    assert report['status'] == 'BLOCKED' and report['unblocked_checks_status'] == 'PASS'
    assert len(report['blocked_checks']) == 17
    assert report['checks']['repository_guard']['status'] == 'PASS'
    assert report['checks']['tests']['skipped'] == 0 and report['checks']['tests']['passed'] >= 347
    assert report['checks']['test_repository_guard']['status'] == 'PASS'
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
    assert report['checks']['committed_source']['commit'] == head, 'report is not from the current committed tree'
    raw = (json.dumps(report, indent=2)+'\n').encode('utf-8')
    target = ROOT/'docs/stage1-gate-public.json'
    target.write_text(raw.decode('utf-8'), encoding='utf-8', newline='\n')
    print(json.dumps(dict(status='RECORDED', file=target.relative_to(ROOT).as_posix(), sha256=sha256(raw).hexdigest())))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    record(parser.parse_args().source)
