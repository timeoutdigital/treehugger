# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import contextlib
import os


@contextlib.contextmanager
def patch_umask(mask):
    old = os.umask(mask)
    yield
    os.umask(old)
