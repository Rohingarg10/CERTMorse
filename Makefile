.PHONY: test test-ttk stage1
ifeq ($(OS),Windows_NT)
PYTHON ?= venv-core/Scripts/python.exe
else
PYTHON ?= python
endif

test:
	$(PYTHON) -m pytest -q -m "not ttk and not tsfm and not gurobi"

test-ttk:
	powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/test.ps1 -Component ttk

stage1:
	powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/measure-r8a.ps1 -Resume
