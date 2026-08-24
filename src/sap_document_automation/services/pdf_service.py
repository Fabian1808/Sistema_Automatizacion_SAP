import time
from pathlib import Path


def wait_for_file(path, timeout=30, poll=0.5):
    path = Path(path)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if path.exists() and path.stat().st_size > 0:
                return True
        except OSError:
            pass
        time.sleep(poll)
    return False


def file_stable(path, interval=0.2, checks=2):
    path = Path(path)
    sizes = set()
    for _ in range(checks):
        try:
            sizes.add(path.stat().st_size)
        except OSError:
            return False
        time.sleep(interval)
    return len(sizes) == 1


def is_valid_pdf(path):
    path = Path(path)
    try:
        with path.open("rb") as fh:
            return fh.read(5) == b"%PDF-"
    except OSError:
        return False


def wait_for_pdf(path, timeout=30, poll=0.5):
    if not wait_for_file(path, timeout=timeout, poll=poll):
        return "El archivo no apareció en la ruta esperada."
    if not file_stable(path):
        return "El archivo todavía se está escribiendo."
    if not is_valid_pdf(path):
        return "El archivo no es un PDF válido."
    return ""
