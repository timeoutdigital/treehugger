import errno

import yaml

from .messaging import die
from .s3 import fetch_s3_content_or_die


def safe_load(fp_or_text):
    obj = yaml.safe_load(fp_or_text)
    return obj


def load_file_or_die(filename):
    if filename.startswith('s3://'):
        return safe_load(fetch_s3_content_or_die(filename))
    try:
        with open(filename, 'r') as fp:
            return safe_load(fp)
    except IOError as exc:
        if exc.errno == errno.ENOENT:
            die('File does not exist!')
        raise


def save_file(filename, data):
    with open(filename, 'w') as fp:
        save_fp(fp, data)


def save_fp(fp, data):
    yaml.safe_dump(
        data,
        fp,
        allow_unicode=True,
        width=10000,
    )


def include_remote_yaml_data_or_die(data):
    """
    Check for "include" key with URL(s), if found fetch & include the yaml
    """
    include_key = 'include'
    if include_key in data:
        url = data.pop(include_key)
        if not isinstance(url, str):
            die("'include' value should be a string")
        yaml_str = fetch_s3_content_or_die(url)
        yaml_data = yaml.safe_load(yaml_str)
        data.update(yaml_data)
    return data
