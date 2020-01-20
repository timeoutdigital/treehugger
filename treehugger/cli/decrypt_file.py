from .. import yaml
from .parser import subparsers
from .utils import load_and_decrypt_file

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
