from unittest import mock

from treehugger.remote import include_remote_yaml_data_or_die


class TestRemote:

    def test_include_remote_yaml_data_or_die(self):

        fetch_counter = [0]  # must be mutable

        def mock_fetch(bucket_name, key, version):
            assert bucket_name == 'bucket'
            assert key == 'filename.yml'
            if fetch_counter[0] == 0:
                assert version is None
            else:
                assert version == '7'
            fetch_counter[0] += 1
            return "X: y"

        with mock.patch('treehugger.remote.fetch_s3_content_or_die', new=mock_fetch):
            data = include_remote_yaml_data_or_die(
                {
                    'A': 'b',
                    'include': [
                        's3://bucket/filename.yml',
                        's3://bucket/filename.yml?versionId=7'
                    ],
                }
            )
            assert data == {'A': 'b', 'X': 'y'}
            assert fetch_counter == [2]
