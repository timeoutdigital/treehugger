# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import io

from treehugger.remote import include_remote_yaml_data_or_die


class TestRemote:

    def test_include_remote_yaml_data_or_die(self, s3_stub):

        s3_stub.add_response(
            'get_object',
            expected_params={
                'Bucket': 'bucketA',
                'Key': 'filename1.yml',
                'VersionId': '1',
            },
            service_response={
                'Body': io.BytesIO(b'X: y'),
            }
        )
        s3_stub.add_response(
            'get_object',
            expected_params={
                'Bucket': 'bucketB',
                'Key': 'filename2.yml',
                'VersionId': '7',
            },
            service_response={
                'Body': io.BytesIO(b'Z: zzz'),
            }
        )

        input_yaml_data = {
            'A': 'b',
            'include': [
                's3://bucketA/filename1.yml?versionId=1',
                's3://bucketB/filename2.yml?versionId=7',
            ],
        }
        assert include_remote_yaml_data_or_die(input_yaml_data) == {
            'A': 'b',
            'X': 'y',
            'Z': 'zzz',
        }
