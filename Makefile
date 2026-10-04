.PHONY: test test-ttk stage1
PYTHON ?= venv-core/Scripts/python.exe

test:
	$(PYTHON) -m pytest -q -m "not ttk and not tsfm and not gurobi"

test-ttk:
	powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/test.ps1 -Component ttk

stage1:
	powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/measure-r8a.ps1 -Resume
