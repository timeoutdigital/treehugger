# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import pytest
import responses

from treehugger.ec2 import USER_DATA_URL, load_user_data_as_yaml_or_die


class TestLoadUserDataAsYamlOrDie:

    @responses.activate
    def test_success(self):
        responses.add(responses.GET, USER_DATA_URL, body='treehugger: {foo: bar}', status=200)
        assert load_user_data_as_yaml_or_die() == {'foo': 'bar'}

    @responses.activate
    def test_connect_error(self, capsys):
        with pytest.raises(SystemExit):
            load_user_data_as_yaml_or_die()

        _, err = capsys.readouterr()
        assert 'Could not connect to EC2 metadata service' in err

    @responses.activate
    def test_404(self, capsys):
        responses.add(responses.GET, USER_DATA_URL, status=404)
        with pytest.raises(SystemExit):
            load_user_data_as_yaml_or_die()

        out, err = capsys.readouterr()
        assert 'Got a 404 from the EC2 metadata service' in err

    @responses.activate
    def test_not_yaml(self, capsys):
        responses.add(responses.GET, USER_DATA_URL, status=200, body='too: many: colons')
        with pytest.raises(SystemExit):
            load_user_data_as_yaml_or_die()

        out, err = capsys.readouterr()
        assert 'Did not find valid YAML in the EC2 user data' in err

    @responses.activate
    def test_not_yaml_dict(self, capsys):
        responses.add(responses.GET, USER_DATA_URL, status=200, body='[1, 2]')
        with pytest.raises(SystemExit):
            load_user_data_as_yaml_or_die()

        out, err = capsys.readouterr()
        assert 'EC2 user data is not a YAML dictionary' in err

    @responses.activate
    def test_missing_treehugger(self, capsys):
        responses.add(responses.GET, USER_DATA_URL, status=200, body='foo: bar')
        with pytest.raises(SystemExit):
            load_user_data_as_yaml_or_die()

        out, err = capsys.readouterr()
        assert 'YAML in EC2 user data does not have a key "treehugger"' in err
