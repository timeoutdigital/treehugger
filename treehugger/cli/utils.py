# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from .. import yaml
from ..data import EnvironmentDict


def load_and_decrypt_file(filename):
    data = yaml.load_file_or_die(filename)

    env_dict = EnvironmentDict.from_yaml_dict(data)
    unencrypted_env_dict = env_dict.decrypt_all_encrypted()
    return unencrypted_env_dict.to_yaml_dict()


def load_and_encrypt_file(filename):
    data = yaml.load_file_or_die(filename)

    env_dict = EnvironmentDict.from_yaml_dict(data)
    encrypted_env_dict = env_dict.encrypt_all_to_encrypt()
    return encrypted_env_dict.to_yaml_dict()
