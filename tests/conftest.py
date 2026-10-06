"""Tests use ignored scratch output and leave repository state unchanged."""
import json
from pathlib import Path
import uuid

import pytest
from scripts.repository_guard import RepositoryGuard

ROOT = Path(__file__).resolve().parents[1]


def pytest_configure(config):
    if config.option.basetemp is None:
        config.option.basetemp = str(ROOT/'results/test-scratch'/uuid.uuid4().hex/'test-tmp')


@pytest.fixture(scope='session', autouse=True)
def repository_guard(tmp_path_factory):
    guard = RepositoryGuard(ROOT)
    guard.activate()
    yield guard
    try:
        report = guard.verify()
    finally:
        guard.active = False
    target = tmp_path_factory.getbasetemp()/'reports/repository-guard.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8', newline='\n')


@pytest.fixture(autouse=True)
def each_test_preserves_repository(repository_guard):
    yield
    repository_guard.verify()
