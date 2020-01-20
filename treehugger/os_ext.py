import contextlib
import os


@contextlib.contextmanager
def patch_umask(mask):
    old = os.umask(mask)
    yield
    os.umask(old)
