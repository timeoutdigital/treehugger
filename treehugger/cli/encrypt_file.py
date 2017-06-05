# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from .. import yaml
from .parser import subparsers
from .utils import load_and_encrypt_file

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
