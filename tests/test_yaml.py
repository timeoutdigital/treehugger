# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from treehugger.yaml import _split_s3_filename


class TestYaml:

    def test_split_s3_filename(self):
        test_s3_filename = 's3://bucket/key?versionId=7'
        assert _split_s3_filename(test_s3_filename) == ('bucket', 'key', '7')
