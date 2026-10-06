"""All test output belongs in ignored repository-relative scratch space."""
from pathlib import Path
import uuid

ROOT = Path(__file__).resolve().parents[1]


def pytest_configure(config):
    if config.option.basetemp is None:
        config.option.basetemp = str(ROOT/'results/test-scratch'/uuid.uuid4().hex/'test-tmp')
