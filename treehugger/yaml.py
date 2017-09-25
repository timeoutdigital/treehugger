# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import errno

import six
import yaml

from .messaging import die


def safe_load(fp_or_text):
    obj = yaml.safe_load(fp_or_text)
    return all_strs_text(obj)


def load_file_or_die(filename):
    try:
        with open(filename, 'r') as fp:
            return safe_load(fp)
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


def all_strs_text(obj):
    """
    PyYAML refuses to load strings as 'unicode' on Python 2 - recurse all over
    obj and convert every string.
    """
    if isinstance(obj, six.binary_type):
        return obj.decode('utf-8')
    elif isinstance(obj, list):
        return [all_strs_text(x) for x in obj]
    elif isinstance(obj, tuple):
        return tuple(all_strs_text(x) for x in obj)
    elif isinstance(obj, dict):
        return {six.text_type(k): all_strs_text(v) for k, v in six.iteritems(obj)}
    else:
        return obj
