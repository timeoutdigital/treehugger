# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
import os

from .. import __version__


class VarOrDefault(object):
    """
    Helper to avoid fetching from environment variable until the moment it's
    needed.
    """
    def __init__(self, env_var, default):
        self.env_var = env_var
        self.default = default

    def __str__(self):
        return os.environ.get(self.env_var, self.default)


parser = argparse.ArgumentParser(
    prog='treehugger',
    description='''
        Takes care of the (runtime) environment. Version {version}.
    '''.format(version=__version__),
)
parser.add_argument(
    '-k',
    '--key',
    type=str,
    default=VarOrDefault('TREEHUGGER_KEY', 'alias/treehugger'),
    dest='key_id',
    help='The key ID, alias, or ARN to use on KMS for encryption.',
)
subparsers = parser.add_subparsers(dest='command_name')
