"""The full-suite guard rejects writes and catches child-process changes."""
import os
from pathlib import Path
import subprocess

import pytest
from scripts.repository_guard import RepositoryGuard, assert_unchanged, snapshot


def sandbox(tmp_path):
    subprocess.run(['git', 'init', '--quiet', str(tmp_path)], check=True)
    path = tmp_path/'evidence.json'
    path.write_text('{}\n', encoding='utf-8', newline='\n')
    subprocess.run(['git', 'add', 'evidence.json'], cwd=tmp_path, check=True)
    return path


def test_guard_rejects_tracked_write_access_before_bytes_change(tmp_path):
    path = sandbox(tmp_path)
    guard = RepositoryGuard(tmp_path)
    guard.active = True
    with pytest.raises(AssertionError, match='never write tracked files'):
        guard.audit('open', (str(path), 'w', os.O_WRONLY | os.O_TRUNC))
    guard.audit('open', (str(path), 'r', os.O_RDONLY))
    assert path.read_bytes() == b'{}\n'


def test_guard_detects_modified_and_created_files(tmp_path):
    path = sandbox(tmp_path)
    before = snapshot(tmp_path)
    path.write_text('{"changed":true}\n', encoding='utf-8', newline='\n')
    with pytest.raises(AssertionError, match='changed tracked files'):
        assert_unchanged(tmp_path, before)
    path.write_text('{}\n', encoding='utf-8', newline='\n')
    (tmp_path/'new-report.json').write_text('{}\n', encoding='utf-8', newline='\n')
    with pytest.raises(AssertionError, match='changed git status'):
        assert_unchanged(tmp_path, before)


def test_full_suite_has_repository_guard(repository_guard):
    assert repository_guard.active
    assert repository_guard.verify()['tracked_hashes_unchanged']
