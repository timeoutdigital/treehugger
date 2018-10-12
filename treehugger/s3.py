# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import boto3
import six
from botocore.exceptions import ClientError
from six.moves.urllib.parse import parse_qs, urlparse

from . import yaml
from .messaging import die

s3_client = boto3.client('s3')


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


def fetch_s3_content_or_die(bucket_name, key, version):
    try:
        s3_response_object = s3_client.get_object(Bucket=bucket_name, Key=key, VersionId=version)
    except ClientError as exc:
        die('Got "{}" when attempting to fetch key {} version {} from bucket {}'.format(
            exc.response['Error']['Code'],
            key,
            version,
            bucket_name,
        ))
    return s3_response_object['Body'].read()


def include_remote_yaml_data_or_die(data):
    """
    Check for "include" key with URL(s), if found fetch & include the yaml
    """
    include_key = 'include'
    if include_key in data:
        url = data.pop(include_key)
        if not isinstance(url, six.string_types):
            die("'include' value should be a string")
        parsed_url = urlparse(url)
        if parsed_url.scheme.lower() != 's3':
            die('Got an unsupported url scheme: {}'.format(parsed_url.scheme))
        bucket_name = parsed_url.netloc
        key = parsed_url.path[1:]
        if not parsed_url.query:
            die('S3 url missing versionId')
        version = parse_qs(parsed_url.query)['versionId'][0]
        yaml_str = fetch_s3_content_or_die(bucket_name, key, version)
        yaml_data = yaml.safe_load(yaml_str)
        data.update(yaml_data)
    return data
