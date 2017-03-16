# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
import os
import subprocess
import sys
import tempfile

from six.moves import shlex_quote

from . import __version__, yaml
from .data import EnvironmentDict
from .ec2 import load_user_data_as_yaml_or_die
from .os_ext import patch_umask

parser = argparse.ArgumentParser(
    prog='treehugger',
    description='''
        Takes care of the (runtime) environment. Version {version}.
    '''.format(version=__version__),
)
subparsers = parser.add_subparsers(dest='command_name')


def main(args_list=None):
    if args_list is None:
        args_list = sys.argv[1:]
    args = parser.parse_args(args_list)
    func = command_funcs[args.command_name]
    func(args)


command_funcs = {}


decrypt_file_parser = subparsers.add_parser(
    'decrypt-file',
    description='Decrypt a Treehugger YAML file in-place.',
)
decrypt_file_parser.add_argument('filename', type=str, help='The path to the file to decrypt')


def decrypt_file(args):
    filename = args.filename

    new_data = load_and_decrypt_file(filename)
    yaml.save_file(filename, new_data)

    print('Successfully decrypted')


command_funcs['decrypt-file'] = decrypt_file


encrypt_file_parser = subparsers.add_parser(
    'encrypt-file',
    description='Encrypt a Treehugger YAML file in-place.'
)
encrypt_file_parser.add_argument('filename', type=str, help='The path to the file to encrypt')


def encrypt_file(args):
    filename = args.filename

    new_data = load_and_encrypt_file(filename)
    yaml.save_file(filename, new_data)

    print('Successfully encrypted')


command_funcs['encrypt-file'] = encrypt_file

edit_parser = subparsers.add_parser(
    'edit',
    description='Decrypt a treehugger YAML file temporarily, edit it with $EDITOR, then re-encrypt it.',
)
edit_parser.add_argument('filename', type=str, help='The path to the file to edit')


def edit(args):
    filename = args.filename

    data = load_and_decrypt_file(filename)

    temp_fp = tempfile.NamedTemporaryFile(suffix='.yml', mode='w', delete=False)
    yaml.save_fp(temp_fp, data)
    temp_fp.flush()
    temp_fp.close()

    with patch_umask(0x077):  # to stop $EDITOR from creating world-readable temp files
        editor = os.environ.get('EDITOR', 'nano')
        retcode = subprocess.call([editor, temp_fp.name])

    if retcode != 0:
        os.unlink(temp_fp.name)
        print('Editor failed with return code {}'.format(retcode), file=sys.stderr)
        raise SystemExit(1)

    new_data = load_and_encrypt_file(temp_fp.name)
    os.unlink(temp_fp.name)

    yaml.save_file(filename, new_data)
    print('Successfully edited file')


command_funcs['edit'] = edit


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


# Helpers


def load_and_decrypt_file(filename):
    data = yaml.load_file_or_die(filename)

    env_dict = EnvironmentDict.from_yaml_dict(data)
    unencrypted_env_dict = env_dict.decrypt_all_encrypted()
    return unencrypted_env_dict.to_yaml_dict()


def load_and_encrypt_file(filename):
    data = yaml.load_file_or_die(filename)

    env_dict = EnvironmentDict.from_yaml_dict(data)
    encrypted_env_dict = env_dict.encrypt_all_to_encrypt()
    return encrypted_env_dict.to_yaml_dict()
