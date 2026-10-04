import os
import subprocess
import csv
import numpy as np
from pathlib import Path


def execute(task,input_path,output_path,*arguments):
    python=os.environ.get('CERTMORSE_PVPYTHON')
    if not python: raise RuntimeError('CERTMORSE_PVPYTHON must name the TTK environment pvpython')
    script=Path(__file__).resolve().parents[1]/'ttk_scripts'/f'{task}.py'
    result=subprocess.run([python,str(script),'--in',str(input_path),'--out',str(output_path),*map(str,arguments)],capture_output=True,text=True,encoding='utf8',errors='replace')
    if result.returncode:
        raise RuntimeError(f'TTK {task} exited {result.returncode}: {result.stderr}')
    return result.stdout


def read_diagram(path):
    diagrams = {q: [] for q in (0,1,2)}
    with open(path, newline='', encoding='utf8') as stream:
        for row in csv.DictReader(stream):
            essential = bool(int(row['is_essential']))
            diagrams[int(row['dim'])].append((float(row['birth']), float('inf') if essential else float(row['death'])))
    return {q: np.asarray(points, dtype=float).reshape(-1,2) for q, points in diagrams.items()}


def read_mandatory(path):
    labels = {}
    with open(path, newline='', encoding='utf8') as stream:
        for row in csv.DictReader(stream):
            labels.setdefault(row['kind'], []).append(int(row['component']))
    counts = {kind: len(set(values)-{-1}) for kind,values in labels.items()}
    return counts, {kind: np.asarray(values) for kind,values in labels.items()}
