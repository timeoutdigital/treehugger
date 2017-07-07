# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import errno

import ruamel.yaml

from .messaging import die

yaml = ruamel.yaml.YAML()
yaml.allow_unicode = True


def load_file_or_die(filename):
    try:
        with open(filename, 'r') as fp:
            return yaml.load(fp)
    except IOError as exc:
        if exc.errno == errno.ENOENT:
            die('File does not exist!')
        raise


def save_file(filename, data):
    with open(filename, 'w') as fp:
        save_fp(fp, data)


def save_fp(fp, data):
    yaml.dump(
        data,
        fp,
    )
