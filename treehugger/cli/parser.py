# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import argparse

from .. import __version__

parser = argparse.ArgumentParser(
    prog='treehugger',
    description='''
        Takes care of the (runtime) environment. Version {version}.
    '''.format(version=__version__),
)
subparsers = parser.add_subparsers(dest='command_name')
