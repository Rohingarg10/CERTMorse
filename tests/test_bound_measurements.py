"""T34 records bounds and times; it does not assert an improvement."""
import importlib.util
from pathlib import Path


def test_T34_archived_bound_measurements():
    path=Path('scripts/bound-measurements.py')
    module_definition=importlib.util.spec_from_file_location('bound_measurements',path)
    module=importlib.util.module_from_spec(module_definition);module_definition.loader.exec_module(module)
    report=module.run(resume=True)
    assert set(report['bands'])=={'hoeffding','m32-0','m32-1','m32-2'}
    assert report['improvement_asserted'] is False
