"""Atomic, input-addressed, append-only computation units (v1.8.4 section 7)."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
SOLVE_SOURCES = (
    'certmorse/complex.py', 'certmorse/forman.py', 'certmorse/scaling.py',
    'certmorse/mip/model_A.py', 'certmorse/mip/model_B.py', 'certmorse/mip/milp.py',
    'certmorse/mip/solvers.py', 'certmorse/mip/compression.py', 'certmorse/mip/regions.py',
    'certmorse/mip/bounds.py', 'certmorse/mip/warm_start.py', 'certmorse/persistence.py',
    'certmorse/ttk.py', 'certmorse/export_vtk.py', 'ttk_scripts/common.py',
    'ttk_scripts/simplify.py', 'configs/instances.yaml', 'certmorse/raw.py',
    'certmorse/landscape.py', 'certmorse/grid.py',
)
LANDSCAPE_SOURCES = (
    'certmorse/landscape.py', 'certmorse/instances.py', 'certmorse/grid.py',
    'certmorse/rng.py', 'certmorse/complex.py', 'certmorse/resolution.py',
    'configs/instances.yaml', 'certmorse/raw.py',
    'scripts/restartable-stage1.py',
)
# The lists are deliberately independent: metrics/scoring changes cannot
# invalidate count solves or multiplicity samples.
UNIT_SOURCES = {
    'solve': SOLVE_SOURCES,
    'sampling': SOLVE_SOURCES+('certmorse/rng.py',),
    'landscape': LANDSCAPE_SOURCES,
    'coverage': LANDSCAPE_SOURCES,
    'scoring': ('certmorse/metrics.py', 'certmorse/complex.py', 'certmorse/forman.py',
                'certmorse/persistence.py', 'certmorse/resolution.py', 'certmorse/mip/regions.py'),
    'optimizer_batch': LANDSCAPE_SOURCES,
    'csv_assembly': (),
}
UNIT_TYPES = {
    name: dict(deterministic=name not in ('solve', 'sampling', 'optimizer_batch'), sources=sources)
    for name, sources in UNIT_SOURCES.items()
}


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def file_hash(path):
    digest = sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def fingerprint(unit_type, config, inputs=None, *, source_root=ROOT):
    if unit_type not in UNIT_SOURCES:
        raise ValueError(f'unknown unit type: {unit_type}')
    if unit_type == 'coverage' and config.get('seed_count', 0) > 100:
        raise ValueError('coverage blocks contain at most 100 seeds')
    # The global digest is provenance, never a cache invalidator.
    resolved = {k: v for k, v in config.items() if k != 'source_digest'}
    sources = {name: file_hash(Path(source_root)/name)
               for name in ('certmorse/units.py',)+UNIT_SOURCES[unit_type]}
    artifacts = {name: file_hash(path) for name, path in sorted((inputs or {}).items())}
    record = dict(unit_type=unit_type, deterministic=UNIT_TYPES[unit_type]['deterministic'],
                  configuration=resolved, input_sha256=artifacts, source_sha256=sources)
    identifier = sha256(json.dumps(record, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()
    return identifier, record


_power_cache = (0, [])


def suspend_intervals():
    """Windows Kernel-Power 42/107 intervals, refreshed at least every minute."""
    global _power_cache
    if os.name != 'nt':
        return []
    now = time.monotonic()
    if now-_power_cache[0] < 60:
        return _power_cache[1]
    command = "$ErrorActionPreference='Stop'; $events=Get-WinEvent -FilterHashtable @{LogName='System'; ProviderName='Microsoft-Windows-Kernel-Power'; Id=42,107} -ErrorAction SilentlyContinue; @($events | Sort-Object TimeCreated | ForEach-Object { @{id=$_.Id; time=$_.TimeCreated.ToUniversalTime().ToString('o')} }) | ConvertTo-Json -Compress"
    result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', command], capture_output=True, text=True, encoding='utf-8')
    if result.returncode:
        raise RuntimeError('cannot audit Windows suspend events: '+result.stderr)
    events = json.loads(result.stdout or '[]')
    if isinstance(events, dict):
        events = [events]
    intervals, start = [], None
    for event in events:
        stamp = datetime.fromisoformat(event['time']).astimezone(timezone.utc)
        if event['id'] == 42:
            start = stamp
        elif start is not None:
            intervals.append((start.isoformat(), stamp.isoformat()))
            start = None
    if start is not None:
        intervals.append((start.isoformat(), utcnow()))
    _power_cache = (now, intervals)
    return intervals


def overlaps_suspend(start, end, intervals):
    a, b = datetime.fromisoformat(start), datetime.fromisoformat(end)
    return any(a <= datetime.fromisoformat(right) and datetime.fromisoformat(left) <= b
               for left, right in intervals)


def complete_unit(folder):
    folder = Path(folder)
    status = folder/'status.json'
    if not status.is_file():
        return False
    try:
        record = json.loads(status.read_text(encoding='utf-8'))
        outputs = record.get('outputs')
        if record.get('complete') is not True or not isinstance(outputs, dict) or not outputs:
            return False
        actual = {p.relative_to(folder).as_posix() for p in folder.rglob('*')
                  if p.is_file() and '.tmp' not in p.relative_to(folder).parts and p != status}
        if actual != set(outputs):
            return False
        return all((folder/name).is_file() and file_hash(folder/name) == digest for name, digest in outputs.items())
    except (ValueError, OSError):
        return False


class SuspendedUnit(RuntimeError):
    pass


class Unit:
    def __init__(self, unit_type, config, inputs=None, *, root='results/units-v1.8.4', suspensions=None):
        self.unit_type = unit_type
        self.config = config
        self.inputs = inputs or {}
        self.root = Path(root).resolve()
        if any('v1.8.3' in part for part in self.root.parts):
            raise ValueError('v1.8.3 results are read-only')
        self.id, self.fingerprint = fingerprint(unit_type, config, self.inputs)
        self.path = (self.root/unit_type/self.id).resolve()
        assert self.path.is_relative_to(self.root)
        self.work = self.path/'.tmp'
        self.suspensions = suspensions

    def intervals(self):
        return suspend_intervals() if self.suspensions is None else self.suspensions

    def _quarantine(self, reason):
        target = (self.root/'quarantine'/f'{self.unit_type}-{self.id}-{uuid.uuid4().hex}').resolve()
        assert self.path.is_relative_to(self.root) and target.is_relative_to(self.root)
        target.parent.mkdir(parents=True, exist_ok=True)
        self.path.rename(target)
        (target/'quarantine.json').write_text(json.dumps(dict(reason=reason, quarantined_at=utcnow()), indent=2), encoding='utf-8', newline='\n')

    def prepare(self):
        if self.path.exists():
            status = self.path/'status.json'
            record = json.loads(status.read_text(encoding='utf-8')) if status.exists() else {}
            start = record.get('started_at')
            end = record.get('completed_at', utcnow())
            if start and overlaps_suspend(start, end, self.intervals()):
                self._quarantine('execution interval overlaps OS suspend')
            elif complete_unit(self.path):
                return False
            elif record.get('complete') is True:
                self._quarantine('completion hashes do not match')
        self.path.mkdir(parents=True, exist_ok=True)
        if self.work.exists():
            assert self.work.resolve().parent == self.path and self.work.resolve().is_relative_to(self.root)
            shutil.rmtree(self.work)
        self.work.mkdir()
        self.started_at = utcnow()
        status = dict(complete=False, unit_id=self.id, unit_type=self.unit_type, started_at=self.started_at)
        (self.work/'status.pending').write_text(json.dumps(status, indent=2), encoding='utf-8', newline='\n')
        (self.work/'status.pending').replace(self.path/'status.json')
        (self.work/'config.json').write_text(json.dumps(dict(**self.fingerprint, unit_id=self.id), indent=2, sort_keys=True), encoding='utf-8', newline='\n')
        return True

    def finish(self, **metadata):
        end = utcnow()
        if overlaps_suspend(self.started_at, end, self.intervals()):
            self._quarantine('execution interval overlaps OS suspend')
            raise SuspendedUnit(self.id)
        files = sorted(p for p in self.work.rglob('*') if p.is_file())
        for source in files:
            target = self.path/source.relative_to(self.work)
            target.parent.mkdir(parents=True, exist_ok=True)
            source.replace(target)
        outputs = {p.relative_to(self.path).as_posix(): file_hash(p) for p in self.path.rglob('*')
                   if p.is_file() and '.tmp' not in p.relative_to(self.path).parts and p != self.path/'status.json'}
        status = dict(complete=True, unit_id=self.id, unit_type=self.unit_type, started_at=self.started_at,
                      completed_at=end, outputs=outputs, **metadata)
        (self.work/'status.json').write_text(json.dumps(status, indent=2, sort_keys=True), encoding='utf-8', newline='\n')
        (self.work/'status.json').replace(self.path/'status.json')
        assert complete_unit(self.path)
        return self.path

    def run(self, function):
        while self.prepare():
            try:
                function(self.work)
                self.finish()
            except SuspendedUnit:
                continue
        return self.path


def test_pause(phase, seed):
    """Hard-kill test rendezvous; inactive unless explicitly armed by T37."""
    if os.environ.get('CERTMORSE_TEST_PAUSE_PHASE') != phase or os.environ.get('CERTMORSE_TEST_PAUSE_SEED') != str(seed):
        return
    marker = Path(os.environ['CERTMORSE_TEST_READY'])
    marker.write_text(json.dumps(dict(phase=phase, seed=seed)), encoding='utf-8', newline='\n')
    while marker.exists():
        time.sleep(.05)
