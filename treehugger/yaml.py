# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import errno

import yaml

from .messaging import die


def load_file_or_die(filename):
    try:
        with open(filename, 'r') as fp:
            return yaml.safe_load(fp)
    except IOError as exc:
        if exc.errno == errno.ENOENT:
            die('File does not exist!')
        raise


def save_file(filename, data):
    with open(filename, 'w') as fp:
        save_fp(fp, data)


def save_fp(fp, data):
    yaml.safe_dump(
        data,
        fp,
        allow_unicode=True,
        width=10000,
    )
