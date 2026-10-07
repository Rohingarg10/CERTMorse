"""Tests use short temporary output and leave repository state unchanged."""
import json
from pathlib import Path

import pytest
from scripts.repository_guard import RepositoryGuard
from scripts.test_scratch import allocate_scratch

ROOT = Path(__file__).resolve().parents[1]


def pytest_configure(config):
    if config.option.basetemp is None:
        config.option.basetemp = str(allocate_scratch())


@pytest.fixture
def tmp_path(tmp_path_factory):
    return tmp_path_factory.mktemp('t')


@pytest.fixture(scope='session', autouse=True)
def repository_guard(tmp_path_factory):
    guard = RepositoryGuard(ROOT)
    guard.activate()
    yield guard
    try:
        report = guard.verify()
        base = tmp_path_factory.getbasetemp()
        report['scratch_longest_path_chars'] = max((len(str(path)) for path in base.rglob('*')), default=len(str(base)))
        assert report['scratch_longest_path_chars'] <= 200, ('scratch path exceeds budget', report['scratch_longest_path_chars'])
    finally:
        guard.active = False
    target = base/'reports/repository-guard.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8', newline='\n')


@pytest.fixture(autouse=True)
def each_test_preserves_repository(repository_guard):
    yield
    repository_guard.verify()
