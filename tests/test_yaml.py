# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import io

from treehugger.yaml import _split_s3_filename, read_file_from_s3


def test_split_s3_filename():
    test_s3_filename = 's3://bucket/key?versionId=7'
    assert _split_s3_filename(test_s3_filename) == ('bucket', 'key', '7')


def test_read_file_from_s3(s3_stub):

    s3_stub.add_response(
        'get_object',
        expected_params={
            'Bucket': 'bucket',
            'Key': 'filename.yml',
            'VersionId': '1',
        },
        service_response={
            'Body': io.BytesIO(b'TREEHUGGER_APP: Test\nTREEHUGGER_STAGE: prod\n'),
        }
    )

    filename = 's3://bucket/filename.yml?versionId=1'
    assert read_file_from_s3(filename) == b'TREEHUGGER_APP: Test\nTREEHUGGER_STAGE: prod\n'
