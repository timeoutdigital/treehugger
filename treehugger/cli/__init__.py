# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import sys

from .decrypt_file import decrypt_file
from .edit import edit
from .execute import execute
from .encrypt_file import encrypt_file
from .parser import parser
from .print_out import print_out


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
    'exec': execute,
    'print': print_out,
}
