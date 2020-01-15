import io

from treehugger.yaml import include_remote_yaml_data_or_die


def test_include_remote_yaml_data_or_die(s3_stub):

    s3_stub.add_response(
        'get_object',
        expected_params={
            'Bucket': 'bucket',
            'Key': 'filename.yml',
            'VersionId': '1',
        },
        service_response={
            'Body': io.BytesIO(b'X: y\nZ: zzz'),
        }
    )
    input_yaml_data = {
        'A': 'b',
        'include': 's3://bucket/filename.yml?versionId=1'
    }
    assert include_remote_yaml_data_or_die(input_yaml_data) == {
        'A': 'b',
        'X': 'y',
        'Z': 'zzz',
    }
