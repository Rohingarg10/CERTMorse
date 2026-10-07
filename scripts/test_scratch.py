"""Short temporary paths for validation, independent of repository depth."""
import os
from pathlib import Path
import tempfile


def allocate_scratch():
    return Path(tempfile.mkdtemp(prefix='cm', dir=tempfile.gettempdir())).resolve()


def report_path(path, repository, scratch):
    """Avoid absolute personal paths in new validation reports."""
    try:
        return Path(os.path.relpath(path, repository)).as_posix()
    except ValueError:
        # Windows roots on different drives have no filesystem-relative path.
        return '<SCRATCH>/'+Path(path).relative_to(scratch).as_posix()
