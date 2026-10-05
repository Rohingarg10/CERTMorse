from pathlib import Path
import json
import pytest
from certmorse.runid import run_id,default_config,prepare_run
from certmorse.rng import restart_streams


def test_T21_identity_and_resume(tmp_path):
    cfg={'seed':7,'instance':'R8a'}
    assert run_id(cfg)==run_id(dict(reversed(list(cfg.items()))))==run_id(default_config(cfg))
    with pytest.raises(ValueError): run_id({'unexpected':1})
    path,execute=prepare_run(cfg,tmp_path,True)
    assert execute
    (path/'partial').write_text('interrupted', encoding='utf-8', newline='\n')
    same,execute=prepare_run(cfg,tmp_path,True)
    assert same==path and execute and not (path/'partial').exists()
    (path/'status.json').write_text(json.dumps({'complete':True}), encoding='utf-8', newline='\n')
    assert prepare_run(cfg,tmp_path,True)==(path,False)


def test_restart_stream_prefix():
    short=restart_streams(7,3)
    long=restart_streams(7,9)
    assert [r.random() for r in short]==[r.random() for r in long[:3]]
