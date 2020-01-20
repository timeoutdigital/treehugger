import pytest

from treehugger.s3 import split_s3_url


def test_split_s3_url():
    test_s3_url = 's3://bucket/key?versionId=7'
    assert split_s3_url(test_s3_url) == ('bucket', 'key', '7')


def test_no_version_split_s3_url():
    test_s3_url = 's3://bucket/key'
    with pytest.raises(SystemExit):
        split_s3_url(test_s3_url)


def test_incorrect_scheme_split_s3_url():
    test_s3_url = 'https://bucket/key?versionId=7'
    with pytest.raises(SystemExit):
        split_s3_url(test_s3_url)
