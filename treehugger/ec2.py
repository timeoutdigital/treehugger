# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import yaml
from requests import Session
from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectionError, ConnectTimeout, HTTPError

from .messaging import die
from .yaml import safe_load

try:
    from urllib3.util.retry import Retry
except ImportError:
    # Requests < 2.16.0
    from requests.packages.urllib3.util.retry import Retry

USER_DATA_URL = 'http://169.254.169.254/latest/user-data'


def load_user_data_as_yaml_or_die(ignore_missing=False):
    try:
        data = load_user_data_as_yaml()
    except (ConnectTimeout, ConnectionError):
        die('Could not connect to EC2 metadata service - are we on an EC2 instance?')
    except HTTPError as exc:
        if exc.response.status_code == 404 and ignore_missing:
            return {'TREEHUGGER_APP': 'Missing', 'TREEHUGGER_STAGE': 'Missing'}

        die('Got a {} from the EC2 metadata service when retrieving user data'.format(exc.response.status_code))
    except yaml.error.YAMLError:
        die('Did not find valid YAML in the EC2 user data')

    try:
        return data['treehugger']
    except TypeError:
        die('EC2 user data is not a YAML dictionary')
    except KeyError:
        die('YAML in EC2 user data does not have a key "treehugger"')


def load_user_data_as_yaml():
    resp = session.get(USER_DATA_URL, timeout=10.0)
    resp.raise_for_status()
    return safe_load(resp.text)


IDENTITY_URL = 'http://169.254.169.254/latest/dynamic/instance-identity/document'


def get_current_region():
    resp = session.get(IDENTITY_URL, timeout=10.0)
    resp.raise_for_status()
    return resp.json()['region']


session = Session()
adapter = HTTPAdapter(max_retries=Retry(
    total=10,
    backoff_factor=0.01,
))
session.mount('http://', adapter)
session.mount('https://', adapter)
