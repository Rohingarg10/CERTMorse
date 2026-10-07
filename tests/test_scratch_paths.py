"""Scratch paths stay short even when a clone is deeply nested."""
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace

import conftest
from certmorse.units import Unit
from scripts.test_scratch import report_path


def test_scratch_paths_stay_under_200_from_a_deep_clone(tmp_path, monkeypatch):
    deep_clone = tmp_path.joinpath(*(['deep-clone-directory']*24), 'repository')
    assert len(str(deep_clone)) > 260
    monkeypatch.setattr(conftest, 'ROOT', deep_clone)
    config = SimpleNamespace(option=SimpleNamespace(basetemp=None))
    conftest.pytest_configure(config)
    base = Path(config.option.basetemp)
    try:
        assert base.parent == Path(tempfile.gettempdir()).resolve()
        assert not base.is_relative_to(deep_clone)
        # Exercise the actual 64-character unit ID and 32-character quarantine
        # suffix with the longest per-test counter needed by the full suite.
        unit = Unit('scoring', dict(seed=1), root=base/'t9999', suspensions=[])
        unit.prepare()
        unit._quarantine('scratch path regression')
        paths = list(base.rglob('*'))
        assert any(path.name == 'quarantine.json' for path in paths)
        assert max(len(str(path)) for path in paths) <= 200
        assert len(tmp_path.name) <= 5
    finally:
        assert base.parent == Path(tempfile.gettempdir()).resolve() and base.name.startswith('cm')
        shutil.rmtree(base)


def test_external_scratch_reports_avoid_absolute_paths(tmp_path):
    reference = tmp_path/'reference'
    repository = Path(tempfile.gettempdir())/'deep'/'clone'
    value = report_path(reference, repository, tmp_path.parent)
    assert not Path(value).is_absolute()
    assert (repository/value).resolve() == reference.resolve()
