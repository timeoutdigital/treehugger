# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import os
import subprocess
import sys
import tempfile

from .. import yaml
from ..os_ext import patch_umask
from .parser import subparsers
from .utils import load_and_decrypt_file, load_and_encrypt_file

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
