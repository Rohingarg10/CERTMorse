"""Reject tracked-file writes and verify that validation leaves Git unchanged."""
from hashlib import sha256
import os
from pathlib import Path
import subprocess
import sys


def git(root, *args):
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0')
    return subprocess.check_output(['git', '-c', 'safe.directory='+str(root), *args], cwd=root, env=env)


def snapshot(root):
    root = Path(root).resolve()
    paths = git(root, 'ls-files', '-z').decode('utf-8').split('\0')[:-1]
    hashes = {}
    for name in paths:
        path = root/name
        hashes[name] = sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    return dict(status=git(root, 'status', '--porcelain=v1', '--untracked-files=all').decode('utf-8'),
                tracked_sha256=hashes)


def assert_unchanged(root, before):
    after = snapshot(root)
    names = set(before['tracked_sha256']) | set(after['tracked_sha256'])
    changed = sorted(name for name in names if before['tracked_sha256'].get(name) != after['tracked_sha256'].get(name))
    assert not changed, ('validation changed tracked files', changed)
    assert after['status'] == before['status'], ('validation changed git status', before['status'], after['status'])
    return dict(status='PASS', before_status=before['status'], after_status=after['status'],
                tracked_files=len(names), tracked_hashes_unchanged=True)


class RepositoryGuard:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.before = snapshot(self.root)
        self.tracked = {os.path.normcase(str((self.root/name).resolve())): name for name in self.before['tracked_sha256']}
        self.active = False

    def audit(self, event, args):
        if not self.active:
            return
        candidates = []
        if event == 'open':
            path, mode, flags = args
            write_flags = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
            if (isinstance(mode, str) and any(c in mode for c in 'wax+')) or flags & write_flags:
                candidates = [path]
        elif event in ('os.remove', 'os.rmdir', 'os.rename', 'os.link', 'os.symlink'):
            candidates = args[:2] if event in ('os.rename', 'os.link', 'os.symlink') else args[:1]
        for value in candidates:
            if not isinstance(value, (str, bytes, os.PathLike)):
                continue
            path = Path(os.fsdecode(value))
            if not path.is_absolute():
                path = Path.cwd()/path
            name = self.tracked.get(os.path.normcase(str(path.resolve())))
            assert name is None, ('tests and gates never write tracked files', name)

    def activate(self):
        self.active = True
        sys.addaudithook(self.audit)

    def verify(self):
        return assert_unchanged(self.root, self.before)
