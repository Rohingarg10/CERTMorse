"""Verify cleaned release archives and restore their saved test fixtures."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import tarfile

ROOT = Path(__file__).resolve().parents[1]
ARCHIVES = {
    'certmorse-results-v0.1.tar.gz': 'results/',
    'certmorse-archive-v0.1.tar.gz': 'docs/archive/',
}


def file_hash(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def checked_name(name, prefix):
    path = PurePosixPath(name)
    if ('\\' in name or path.is_absolute() or any(p in ('', '.', '..') for p in name.split('/'))
            or not name.startswith(prefix) or any(':' in p for p in path.parts)):
        raise ValueError('Unsafe release member: '+name)
    if any(p.lower() in ('test-tmp', 'test-scratch', '.pytest_cache', '__pycache__') or
           p.lower().startswith('pytest-of-') for p in path.parts):
        raise ValueError('Test scratch member: '+name)
    return path


def unpack(path, prefix):
    checksum = path.with_name(path.name+'.sha256').read_text(encoding='utf-8').strip()
    expected, name = checksum.split('  ', 1)
    if name != path.name or not re.fullmatch('[0-9a-f]{64}', expected) or file_hash(path) != expected:
        raise ValueError('Archive checksum mismatch: '+path.name)
    manifest_name = prefix+'SHA256SUMS.release'
    with tarfile.open(path, 'r:gz') as archive:
        members = archive.getmembers()
        names = [m.name for m in members]
        if len(set(names)) != len(names) or not all(m.isfile() for m in members):
            raise ValueError('Duplicate or non-file archive member')
        for member in members:
            checked_name(member.name, prefix)
        stream = archive.extractfile(manifest_name)
        if stream is None:
            raise ValueError('Missing release manifest')
        entries = {}
        for line in stream.read().decode('utf-8').splitlines():
            digest, name = line.split('  ', 1)
            checked_name(name, prefix)
            if name in entries or not re.fullmatch('[0-9a-f]{64}', digest):
                raise ValueError('Malformed release manifest')
            entries[name] = digest
        if set(entries) != set(names)-{manifest_name}:
            raise ValueError('Manifest does not cover exactly the release members')
        for member in members:
            if member.name == manifest_name:
                continue
            with archive.extractfile(member) as source:
                if hashlib.file_digest(source, 'sha256').hexdigest() != entries[member.name]:
                    raise ValueError('Member checksum mismatch: '+member.name)
        created = unchanged = 0
        for member in members:
            target = (ROOT/member.name).resolve()
            if not target.is_relative_to(ROOT.resolve()):
                raise ValueError('Member escapes repository')
            with archive.extractfile(member) as source:
                if target.exists():
                    digest = hashlib.file_digest(source, 'sha256').hexdigest()
                    if not target.is_file() or file_hash(target) != digest:
                        raise ValueError('Refusing to overwrite different bytes: '+member.name)
                    unchanged += 1
                    continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.extractfile(member) as source, target.open('xb') as destination:
                shutil.copyfileobj(source, destination)
            created += 1
    return dict(archive=path.name, sha256=expected, members=len(members),
                created=created, identical_existing=unchanged, overwritten=0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('assets', type=Path)
    args = parser.parse_args()
    print(json.dumps([unpack(args.assets/name, prefix) for name, prefix in ARCHIVES.items()]))
