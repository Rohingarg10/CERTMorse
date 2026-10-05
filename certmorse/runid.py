from pathlib import Path
from hashlib import sha256
from copy import deepcopy
from .provenance import source_digest
import json
import shutil
import yaml

DEFAULTS={
    'implementation_revision':'stage1-v1.8.3',
    'source_digest':None,
    'experiment':'E1','instance':'R8a','grid_m':32,'noise':'a','shots':1000,
    'band_mode':'hoeffding','alpha':.05,'seed':7,'solver':'cpsat','formulation':'A',
    'warm_start':True,'time_limit_s':600,'threads':8,'repeats':1,
    'optimizer':{'names':['cobyla','nelder_mead','gd'],'restarts':500,'eval_mode':'exact','eval_shots':1000},
    'forecast':{'checkpoint':'google/timesfm-3.0-pytorch','k':[20,40,80],
                'covariates':True,'quantile_index':0,'batch_size':32,
                'max_series':40000,'recall_target':.95},
    'multiplicity':{'enabled':False,'max_optima':20,'time_cap_s':300},
    'allocation':{'arm':'adaptive','n0':200,'n_max_per_vertex':30000,'r_max':20},
}


def default_config(cfg):
    def merge(default,provided):
        unknown=set(provided)-set(default)
        if unknown: raise ValueError(f'unknown configuration keys: {sorted(unknown)}')
        result=deepcopy(default)
        for k,v in provided.items():
            result[k]=merge(default[k],v) if isinstance(default[k],dict) else v
        return result
    result=merge(DEFAULTS,cfg)
    if result['source_digest'] is None: result['source_digest']=source_digest()
    return result


def canonical_config(cfg):
    return yaml.safe_dump(default_config(cfg),sort_keys=True,default_flow_style=False)


def run_id(cfg):
    return sha256(canonical_config(cfg).encode('utf8')).hexdigest()[:12]


def prepare_run(cfg,root='results',resume=False):
    cfg=default_config(cfg)
    root=Path(root).resolve()
    target=(root/cfg['experiment']/run_id(cfg)).resolve()
    if not target.is_relative_to(root): raise ValueError('run path escapes results directory')
    if target.exists():
        status=target/'status.json'
        complete=status.exists() and json.loads(status.read_text(encoding='utf8')).get('complete') is True
        if resume and complete: return target,False
        if resume:
            shutil.rmtree(target)
        else:
            raise FileExistsError('run exists; use --resume or the dedicated .rerun reproducibility directory')
    target.mkdir(parents=True)
    (target/'config.yaml').write_text(canonical_config(cfg),encoding='utf-8', newline='\n')
    (target/'status.json').write_text(json.dumps({'complete':False}),encoding='utf-8', newline='\n')
    return target,True
