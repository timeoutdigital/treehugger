from urllib.parse import parse_qs, urlparse

import boto3
from botocore.exceptions import ClientError

from .messaging import die

s3_client = boto3.client('s3')


def fetch_s3_content_or_die(url):
    bucket_name, key, version = split_s3_url(url)
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


def split_s3_url(url):
    parsed_url = urlparse(url)
    if parsed_url.scheme.lower() != 's3':
        die('Got an unsupported url scheme: {}'.format(parsed_url.scheme))
    bucket_name = parsed_url.netloc
    bucket_key = parsed_url.path[1:]
    if not parsed_url.query:
        die('S3 url missing versionId')
    version = parse_qs(parsed_url.query)['versionId'][0]
    return bucket_name, bucket_key, version
