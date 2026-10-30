"""Read-only disk-space preflight for large owned capture cohorts."""
from pathlib import Path
import shutil

def require_space(output,minimum_bytes):
    if minimum_bytes<=0:raise ValueError('Space requirement must be positive')
    path=Path(output).resolve()
    while not path.exists():
        parent=path.parent
        if parent==path:raise ValueError('No existing output ancestor')
        path=parent
    free=shutil.disk_usage(path).free
    if free<minimum_bytes:raise OSError(f'Insufficient capture space: require {minimum_bytes} bytes; available {free}. Choose a new output volume; preserve existing evidence.')
    return dict(required_bytes=minimum_bytes,available_bytes=free,scope='Preflight estimate, not a reservation or guarantee against other writers')
