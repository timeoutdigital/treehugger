# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
import os
import sys

from six.moves import shlex_quote

from .decrypt_file import decrypt_file
from .edit import edit
from .encrypt_file import encrypt_file
from .parser import parser, subparsers
from .. import yaml
from ..data import EnvironmentDict
from ..ec2 import load_user_data_as_yaml_or_die


def main(args_list=None):
    if args_list is None:
        args_list = sys.argv[1:]
    args = parser.parse_args(args_list)
    func = command_funcs[args.command_name]
    func(args)


command_funcs = {
    'decrypt-file': decrypt_file,
    'encrypt-file': encrypt_file,
    'edit': edit,
}


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


def execute(args):
    command = args.command
    if command and command[0] == '--':
        command = command[1:]
    if not command:
        print('No command to execute provided', file=sys.stderr)
        raise SystemExit(1)

    if args.filename:
        data = yaml.load_file_or_die(args.filename)
        env_dict = EnvironmentDict.from_yaml_dict(data)
    else:
        data = load_user_data_as_yaml_or_die()
        env_dict = EnvironmentDict.from_yaml_dict(data)
    unencrypted_env_dict = env_dict.decrypt_all_encrypted(plain=True)
    os.environ.update(unencrypted_env_dict)
    os.execlp(command[0], *command)


command_funcs['exec'] = execute


print_parser = subparsers.add_parser(
    'print',
    description='''
        Print all environment variables, from EC2 User Data or a file.
    ''',
)
print_parser.add_argument('-f', '--file', type=str, default=None, dest='filename',
                          help='The path to the file to use for environment variables, as opposed to EC2 User Data')
print_parser.add_argument('--only-unencrypted', action='store_true',
                          help="Ignore encrypted variables and only output those that aren't encrypted")
print_parser.add_argument('--single-line', action='store_true',
                          help='Output all the variables on a single line, separated by spaces')


def print_(args):
    if args.filename:
        data = yaml.load_file_or_die(args.filename)
        env_dict = EnvironmentDict.from_yaml_dict(data)
    else:
        data = load_user_data_as_yaml_or_die()
        env_dict = EnvironmentDict.from_yaml_dict(data)

    if args.only_unencrypted:
        unencrypted_env_dict = env_dict.remove_all_encrypted(plain=True)
    else:
        unencrypted_env_dict = env_dict.decrypt_all_encrypted(plain=True)

    output = [
        '{}={}'.format(key, shlex_quote(value))
        for key, value in sorted(unencrypted_env_dict.items())
    ]

    if args.single_line:
        joiner = ' '
    else:
        joiner = '\n'

    print(joiner.join(output))


command_funcs['print'] = print_
