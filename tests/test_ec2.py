import pytest
import requests

from treehugger.ec2 import USER_DATA_URL, load_user_data_as_yaml_or_die


def test_success(requests_mock):
    requests_mock.get(USER_DATA_URL, text='treehugger: {foo: bar}', status_code=200)
    assert load_user_data_as_yaml_or_die() == {'foo': 'bar'}


def test_connect_error(requests_mock, capsys):
    requests_mock.get(USER_DATA_URL, exc=requests.exceptions.ConnectTimeout)
    with pytest.raises(SystemExit):
        load_user_data_as_yaml_or_die()

    _, err = capsys.readouterr()
    assert 'Could not connect to EC2 metadata service' in err


def test_404(requests_mock, capsys):
    requests_mock.get(USER_DATA_URL, status_code=404)
    with pytest.raises(SystemExit):
        load_user_data_as_yaml_or_die()

    out, err = capsys.readouterr()
    assert 'Got a 404 from the EC2 metadata service' in err


def test_not_yaml(requests_mock, capsys):
    requests_mock.get(USER_DATA_URL, status_code=200, text='too: many: colons')
    with pytest.raises(SystemExit):
        load_user_data_as_yaml_or_die()

    out, err = capsys.readouterr()
    assert 'Did not find valid YAML in the EC2 user data' in err


def test_not_yaml_dict(requests_mock, capsys):
    requests_mock.get(USER_DATA_URL, status_code=200, text='[1, 2]')
    with pytest.raises(SystemExit):
        load_user_data_as_yaml_or_die()

    out, err = capsys.readouterr()
    assert 'EC2 user data is not a YAML dictionary' in err


def test_missing_treehugger(requests_mock, capsys):
    requests_mock.get(USER_DATA_URL, status_code=200, text='foo: bar')
    with pytest.raises(SystemExit):
        load_user_data_as_yaml_or_die()

    out, err = capsys.readouterr()
    assert 'YAML in EC2 user data does not have a key "treehugger"' in err
