# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import boto3
from botocore.exceptions import ClientError

from six.moves.urllib.parse import parse_qs, urlparse

from . import yaml
from .messaging import die

# initialise client here so can be stubbed for testing
s3_client = boto3.client('s3')


def fetch_s3_content_or_die(bucket_name, key, version=None):
    if not version:
        version = 'null'
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
        url_data = data.pop(include_key)
        # accept either a single url as value, or list of url values
        if not isinstance(url_data, list):
            url_data = [url_data]
        for url in url_data:
            parsed_url = urlparse(url)
            if parsed_url.scheme.lower() == 's3':
                bucket_name = parsed_url.netloc
                key = parsed_url.path[1:]
                if parsed_url.query:
                    version = parse_qs(parsed_url.query)['versionId'][0]
                else:
                    version = None
                yaml_str = fetch_s3_content_or_die(bucket_name, key, version)
                yaml_data = yaml.safe_load(yaml_str)
                data.update(yaml_data)
            else:
                die('Got an unsupported url scheme: {}'.format(parsed_url.scheme))
    return data
