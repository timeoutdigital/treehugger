# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import errno

import boto3
import six
import yaml
from botocore.exceptions import ClientError
from six.moves.urllib.parse import parse_qs, urlparse

from .messaging import die

s3_client = boto3.client('s3')


def safe_load(fp_or_text):
    obj = yaml.safe_load(fp_or_text)
    return all_strs_text(obj)


def _split_s3_filename(s3_key):
    parsed_url = urlparse(s3_key)
    if parsed_url.scheme.lower() != 's3':
        die('Got an unsupported url scheme: {}'.format(parsed_url.scheme))
    bucket_name = parsed_url.netloc
    bucket_key = parsed_url.path[1:]
    version = parse_qs(parsed_url.query)['versionId'][0]
    return bucket_name, bucket_key, version


def read_file_from_s3(filename):
    bucket_name, bucket_key, version = _split_s3_filename(filename)
    try:
        obj = s3_client.get_object(
            Bucket=bucket_name,
            Key=bucket_key,
            VersionId=version,
        )
    except ClientError as exc:
        die('Got "{}" when attempting to fetch key {} version {} from bucket {}'.format(
            exc.response['Error']['Code'],
            bucket_key,
            version,
            bucket_name,
        ))
    return obj['Body'].read()


def load_file_or_die(filename):
    if filename.startswith('s3://'):
        return safe_load(read_file_from_s3(filename))
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


def all_strs_text(obj):
    """
    PyYAML refuses to load strings as 'unicode' on Python 2 - recurse all over
    obj and convert every string.
    """
    if isinstance(obj, six.binary_type):
        return obj.decode('utf-8')
    elif isinstance(obj, list):
        return [all_strs_text(x) for x in obj]
    elif isinstance(obj, tuple):
        return tuple(all_strs_text(x) for x in obj)
    elif isinstance(obj, dict):
        return {six.text_type(k): all_strs_text(v) for k, v in six.iteritems(obj)}
    else:
        return obj
