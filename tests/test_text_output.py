"""Text output must have identical encoding and line endings on every OS."""
import ast
import importlib.util
import json
from pathlib import Path
import shutil

import yaml

from certmorse.runid import prepare_run

ROOT = Path(__file__).resolve().parents[1]
CODE_ROOTS = ('certmorse', 'scripts', 'ttk_scripts', 'tsfm_scripts', 'tests', 'prototypes')


def violations(source):
    errors = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        name = node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id if isinstance(node.func, ast.Name) else ''
        write = name == 'write_text'
        keywords = {kw.arg: kw.value for kw in node.keywords}
        if name == 'open':
            position = 1 if isinstance(node.func, ast.Name) else 0
            mode = keywords.get('mode', node.args[position] if len(node.args) > position else ast.Constant('r'))
            if not isinstance(mode, ast.Constant):
                errors.append((node.lineno, 'dynamic open mode requires review'))
                continue
            write = 'b' not in mode.value and any(c in mode.value for c in 'wax+')
        required = {'encoding': 'utf-8', 'newline': '\n'} if write else {'lineterminator': '\n'} if name in ('DictWriter', 'writer') else {}
        for key, value in required.items():
            actual = keywords.get(key)
            if not isinstance(actual, ast.Constant) or actual.value != value:
                errors.append((node.lineno, f'{name} requires {key}={value!r}'))
    return errors


def test_all_text_writes_are_explicit_utf8_lf():
    errors = []
    for directory in CODE_ROOTS:
        for path in sorted((ROOT/directory).rglob('*.py')):
            errors.extend((path.relative_to(ROOT).as_posix(), *error) for error in violations(path.read_text(encoding='utf-8')))
    assert not errors, errors
    assert violations("p.write_text('x')")
    assert violations("open('x', 'w', encoding='utf-8')")
    assert violations("csv.DictWriter(stream, fieldnames=['x'])")
    assert not violations("open('x', 'wb')")


def test_regenerated_report_and_yaml_have_no_carriage_return(tmp_path, monkeypatch):
    docs = tmp_path/'docs'
    (docs/'archive/v1.7').mkdir(parents=True)
    for name in ('T34-v1.8.3.json', 'T31-v1.8.3.json', 'resolution-v1.8.3.json'):
        shutil.copyfile(ROOT/'docs'/name, docs/name)
    shutil.copyfile(ROOT/'docs/archive/v1.7/CERTIFICATE.md', docs/'archive/v1.7/CERTIFICATE.md')
    gate = json.loads((ROOT/'docs/stage1-gate.json').read_text(encoding='utf-8'))
    gate['steps'] = []
    (docs/'stage1-gate.json').write_text(json.dumps(gate), encoding='utf-8', newline='\n')
    monkeypatch.chdir(tmp_path)
    spec = importlib.util.spec_from_file_location('report_stage1', ROOT/'scripts/report-stage1.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.run()
    report = docs/'STAGE1.md'
    assert report.read_bytes().startswith(b'# Stage 1 evidence')
    assert b'\r' not in report.read_bytes()
    output, needed = prepare_run({'experiment': 'text-output-test', 'grid_m': 4}, root=tmp_path/'results')
    assert needed
    config = output/'config.yaml'
    assert yaml.safe_load(config.read_text(encoding='utf-8'))['grid_m'] == 4
    assert b'\r' not in config.read_bytes()


def test_powershell_text_writes_use_lf_helper():
    for path in (ROOT/'scripts').glob('*.ps1'):
        source = path.read_text(encoding='utf-8')
        assert 'Set-Content' not in source and 'Out-File' not in source and 'WriteAllLines' not in source, path
        if 'WriteAllText' in source:
            assert path.name == 'text-output.ps1'
            assert '[Text.UTF8Encoding]::new($false)' in source
            assert '.Replace("`r`n", "`n").Replace("`r", "`n")' in source
