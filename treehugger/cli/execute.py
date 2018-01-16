# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
import os
import sys

from .. import yaml
from ..data import EnvironmentDict
from ..ec2 import load_user_data_as_yaml_or_die
from ..remote import include_remote_yaml_data_or_die
from .parser import subparsers

exec_parser = subparsers.add_parser(
    'exec',
    description='''
        Execute a command with environment variables set to the decryption of
        the variables stored in Treehugger YAML in EC2 User Data, or a file.
    ''',
)
exec_parser.add_argument('-f', '--file', type=str, default=None, dest='filename',
                         help='The path to the file to use for environment variables, as opposed to EC2 User Data')
exec_parser.add_argument('command', nargs=argparse.REMAINDER)

exec_parser.add_argument('-i', '--ignore-missing', action='store_true', dest='ignoremissing',
                         help="Don't die if there are no variables")


def execute(args):
    command = args.command
    if command and command[0] == '--':
        command = command[1:]
    if not command:
        print('No command to execute provided', file=sys.stderr)
        raise SystemExit(1)

    if args.filename:
        data = yaml.load_file_or_die(args.filename)
    else:
        data = load_user_data_as_yaml_or_die(args.ignoremissing)
    data = include_remote_yaml_data_or_die(data)
    env_dict = EnvironmentDict.from_yaml_dict(data)
    unencrypted_env_dict = env_dict.decrypt_all_encrypted(plain=True)
    os.environ.update(unencrypted_env_dict)
    os.execlp(command[0], *command)
