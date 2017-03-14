# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import sys


def die(message):
    print(message, file=sys.stderr)
    raise SystemExit(1)
