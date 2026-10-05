"""T38 first, then append-only re-scoring and v1.8.4 CSV assembly."""
import csv
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from certmorse.legacy_scores import verify_T38, stage1_folders, saved_path
from certmorse.raw import write_json
from certmorse.scoring import score_folder
from certmorse.units import ROOT, Unit, file_hash


def csv_table(rows, destination, inputs):
    unit = Unit('csv_assembly', dict(destination=Path(destination).name), inputs, root=ROOT/'results/stage1-tables-v1.8.4')
    def run(work):
        fields = list(dict.fromkeys(key for row in rows for key in row))
        with (work/Path(destination).name).open('w', encoding='utf-8', newline='\n') as stream:
            writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
            writer.writeheader(); writer.writerows(rows)
    path = unit.run(run)/Path(destination).name
    target = Path(destination)
    if target.exists():
        assert target.read_bytes() == path.read_bytes(), f'complete table differs: {target}'
    else:
        temp = target.with_name(target.name+'.tmp')
        temp.write_bytes(path.read_bytes()); temp.replace(target)
    return path


def run():
    # No scoring unit or new data column can be written before this succeeds
    # across the entire saved gate, not just the folder about to be scored.
    reproduction = verify_T38()
    write_json(ROOT/'docs/T38-v1.8.4.json', reproduction)
    datasets, inputs, sidecars = {}, {}, []
    for folder, base in stage1_folders():
        row, scored = score_folder(folder, base)
        label = row['instance'].lower()+'-'+row['band_mode']
        datasets.setdefault(label, []).append(row)
        inputs.setdefault(label, {})[folder.name] = scored/'measurement-v1.8.4.json'
        if base.get('multiplicity_run_path'):
            _, side = score_folder(folder, base, sampling_folder=saved_path(base['multiplicity_run_path']))
            sidecars.append(dict(primary=folder.relative_to(ROOT).as_posix(),
                                 sampling=base['multiplicity_run_path'], scoring=side.relative_to(ROOT).as_posix()))
    for label, rows in datasets.items():
        name, mode = label.split('-')
        csv_table(rows, ROOT/f'docs/stage1-{name}-{mode}-rescored-v1.8.4.csv', inputs[label])
    report = dict(status='PASS', folders=sum(map(len, datasets.values())), sidecar_folders=len(sidecars),
                  sidecar_scoring=sidecars, T38=True,
                  tables={key: f'docs/stage1-{key}-rescored-v1.8.4.csv' for key in datasets},
                  input_sha256=reproduction['input_sha256'])
    write_json(ROOT/'docs/rescoring-v1.8.4.json', report)
    print(json.dumps(dict(status='PASS', folders=report['folders'], datasets=list(datasets))))
    return report


if __name__ == '__main__':
    run()
