"""Content identity for the implementation used by a run."""
from hashlib import sha256
from pathlib import Path


def source_digest():
    root=Path(__file__).resolve().parents[1]
    paths=list((root/'certmorse').rglob('*.py'))+list((root/'ttk_scripts').rglob('*.py'))+[root/'configs/instances.yaml']
    digest=sha256()
    for path in sorted(paths):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b'\0');digest.update(path.read_bytes());digest.update(b'\0')
    return digest.hexdigest()
