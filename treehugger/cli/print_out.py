# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from six.moves import shlex_quote

from .. import yaml
from ..data import EnvironmentDict
from ..ec2 import load_user_data_as_yaml_or_die
from .parser import subparsers

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
print_parser.add_argument('--export', action='store_true',
                          help='Output all the variables in a way that can be evaulated by sh')

def print_out(args):
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

    fmt = '{}={}'.format
    if args.export:
        fmt = 'export {}={};'.format
    output = [
        fmt(key, shlex_quote(value))
        for key, value in sorted(unencrypted_env_dict.items())
    ]

    if args.single_line:
        joiner = ' '
    else:
        joiner = '\n'

    print(joiner.join(output))
