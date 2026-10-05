"""Re-score completed oracle artefacts; never invoke a solver or sampler."""
import importlib.util
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from certmorse.legacy_scores import stage1_folders, verify_T38
from certmorse.raw import write_json
from certmorse.scoring import score_folder
from certmorse.stage1_scoring import oracle_row
from certmorse.units import ROOT, complete_unit, file_hash

spec = importlib.util.spec_from_file_location('rescore', ROOT/'scripts/rescore-stage1.py')
rescore = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rescore)


def location(name):
    path = Path(name)
    return path if path.is_absolute() else ROOT/path


def snapshot(report):
    folders = set()
    for instance, dataset in report['records'].items():
        for band in dataset['bands']:
            if instance != 'R8a':
                folders.add(location(band['raw']))
            if band['sampling'] is not None:
                folders.add(location(band['sampling']))
    result = {}
    for folder in folders:
        assert complete_unit(folder), folder
        result[folder.relative_to(ROOT).as_posix()] = file_hash(folder/'status.json')
    return result


def run():
    verify_T38()
    destination = ROOT/'docs/oracle-completion-v1.8.4.json'
    report = json.loads(destination.read_text(encoding='utf-8'))
    assert report['status'] == 'PASS'
    preserved = ROOT/'docs/oracle-completion-original-v1.8.4.json'
    if not preserved.exists():
        preserved.write_bytes(destination.read_bytes())
    before = snapshot(report)
    legacy = {(row['instance'], row['band_mode'], row['seed']): row for _, row in stage1_folders()}
    tables = {}
    for instance, dataset in report['records'].items():
        rows, inputs = [], {'assembly_driver': Path(__file__)}
        for band in dataset['bands']:
            folder = location(band['raw'])
            sampling = None if band['sampling'] is None else location(band['sampling'])
            mode = 'oracle' if instance == 'R8a' else 'hoeffding'
            base = dict(legacy[instance, mode, band['seed']])
            if instance == 'R8a':
                base.update(raw_unit_id=folder.name, sampling_unit_id=None if sampling is None else sampling.name)
                row, scored = score_folder(folder, base, sampling_folder=sampling)
            else:
                row, scored = oracle_row(folder, base, sampling_folder=sampling)
            assert 'raw_path' not in row and 'sampling_path' not in row
            rows.append(row)
            inputs[str(band['seed'])] = scored/'measurement-v1.8.4.json'
            band.update(raw=folder.relative_to(ROOT).as_posix(), scoring=scored.relative_to(ROOT).as_posix(),
                        sampling=None if sampling is None else sampling.relative_to(ROOT).as_posix())
        name = f'docs/stage1-{instance.lower()}-oracle-completion-rescored-v1.8.4.csv'
        rescore.csv_table(rows, ROOT/name, inputs)
        tables[instance] = name
    after = snapshot(report)
    assert before == after, 'a completed raw unit changed during scoring'
    report.update(tables=tables, tables_sha256={instance: file_hash(ROOT/name) for instance, name in tables.items()},
                  raw_units_preserved=True, portable_unit_identifiers=True)
    write_json(destination, report)
    write_json(ROOT/'docs/oracle-rescoring-v1.8.4.json', dict(status='PASS', raw_units_preserved=len(before),
               raw_status_sha256=before, original_report_sha256=file_hash(preserved), tables=tables))
    print(json.dumps(dict(status='PASS', raw_units_preserved=len(before), tables=tables)), flush=True)


if __name__ == '__main__':
    run()
