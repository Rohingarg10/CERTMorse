import os
import subprocess
from pathlib import Path
import json
import pytest


@pytest.mark.tsfm
@pytest.mark.skipif(not os.environ.get('CERTMORSE_TSFM_PYTHON'),reason='configure the TimesFM environment')
def test_T17_cpu_wrapper(tmp_path):
    env=os.environ.copy();env['HF_HUB_OFFLINE']='1'
    result=subprocess.run([env['CERTMORSE_TSFM_PYTHON'],'tsfm_scripts/forecast.py','--smoke','--out',str(tmp_path/'smoke.json')],env=env,capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    assert json.loads((tmp_path/'smoke.json').read_text())['T17']=='passed'
