# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import six

from .kms import kms_agent


class EnvironmentDict(dict):

    @classmethod
    def from_yaml_dict(cls, obj):
        """
        Construct an EnvironmentDict from the plain data loaded from YAML, e.g.

        {
            'MY_VAR': {'encrypted': 'blablabla'}
        }

        Would become

        EnvironmentDict(
            MY_VAR=Encrypted('blablabla')
        )
        """
        assert isinstance(obj, dict)
        new = EnvironmentDict()
        for key, value in obj.items():
            assert isinstance(key, six.string_types), "Keys must be strings in treehugger data"
            if isinstance(value, dict):
                if 'to_encrypt' in value:
                    new_value = ToEncrypt(value['to_encrypt'])
                elif 'encrypted' in value:
                    new_value = Encrypted(value['encrypted'])
            elif isinstance(value, six.string_types):
                new_value = value
            else:
                raise ValueError('Invalid object in treehugger data: {}'.format(value))
            new[key] = new_value
        return new

    def to_yaml_dict(self):
        new = {}
        for key, value in self.items():
            if isinstance(value, six.string_types):
                new[key] = value
            elif isinstance(value, ToEncrypt):
                new[key] = {'to_encrypt': value.plaintext}
            elif isinstance(value, Encrypted):
                new[key] = {'encrypted': value.base64_ciphertext}
            else:
                raise ValueError("Invalid object in EnvironmentDict: {}".format(value))
        return new

    def decrypt_all_encrypted(self, plain=False):
        base_encryption_context = self.get_base_encryption_context()
        new = EnvironmentDict()
        for key, value in self.items():
            if isinstance(value, Encrypted):
                encryption_context = base_encryption_context.copy()
                encryption_context['treehugger_key'] = key
                plaintext = kms_agent.decrypt(value.base64_ciphertext, encryption_context)
                if plain:
                    new[key] = plaintext
                else:
                    new[key] = ToEncrypt(plaintext)
            elif isinstance(value, ToEncrypt):
                if plain:
                    new[key] = value.plaintext
                else:
                    new[key] = value
            else:
                new[key] = value
        return new

    def encrypt_all_to_encrypt(self):
        base_encryption_context = self.get_base_encryption_context()
        new = EnvironmentDict()
        for key, value in self.items():
            if isinstance(value, ToEncrypt):
                encryption_context = base_encryption_context.copy()
                encryption_context['treehugger_key'] = key
                base64_ciphertext = kms_agent.encrypt(value.plaintext, encryption_context)
                new[key] = Encrypted(base64_ciphertext)
            else:
                new[key] = value
        return new

    def remove_all_encrypted(self, plain=False):
        new = EnvironmentDict()
        for key, value in self.items():
            if isinstance(value, Encrypted):
                pass
            elif isinstance(value, ToEncrypt):
                if plain:
                    new[key] = value.plaintext
                else:
                    new[key] = value
            else:
                new[key] = value
        return new

    def get_base_encryption_context(self):
        try:
            app = self['TREEHUGGER_APP']
            stage = self['TREEHUGGER_STAGE']
        except KeyError as exc:
            raise ValueError('Missing {}'.format(exc.args[0]))
        return {
            'treehugger_app': app,
            'treehugger_stage': stage,
        }


class ToEncrypt(object):
    def __init__(self, plaintext):
        assert isinstance(plaintext, six.text_type)
        self.plaintext = plaintext

    def __eq__(self, other):
        return (
            self.__class__ is other.__class__ and
            self.plaintext == other.plaintext
        )


class Encrypted(object):
    def __init__(self, base64_ciphertext):
        assert isinstance(base64_ciphertext, six.text_type)
        self.base64_ciphertext = base64_ciphertext

    def __eq__(self, other):
        return (
            self.__class__ is other.__class__ and
            self.base64_ciphertext == other.base64_ciphertext
        )
