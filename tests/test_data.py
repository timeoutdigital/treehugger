# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import base64

import pytest

from treehugger.data import Encrypted, EnvironmentDict, ToEncrypt


class TestEnvironmentDict:

    def test_from_yaml_dict_success_plain(self):
        obj = EnvironmentDict.from_yaml_dict({'foo': 'bar'})
        assert obj == EnvironmentDict({'foo': 'bar'})

    def test_from_yaml_dict_success_to_encrypt(self):
        obj = EnvironmentDict.from_yaml_dict({'foo': {'to_encrypt': 'foo'}})
        assert obj == EnvironmentDict({'foo': ToEncrypt('foo')})

    def test_from_yaml_dict_success_encrypted(self):
        obj = EnvironmentDict.from_yaml_dict({'foo': {'encrypted': 'foo'}})
        assert obj == EnvironmentDict({'foo': Encrypted('foo')})

    def test_from_yaml_dict_fail_bad_type(self):
        with pytest.raises(AssertionError):
            EnvironmentDict.from_yaml_dict('not a dict')

    def test_from_yaml_dict_fail_key_not_string(self):
        with pytest.raises(AssertionError):
            EnvironmentDict.from_yaml_dict({1: 'not string key'})

    def test_from_yaml_dict_fail_value_unknown(self):
        with pytest.raises(ValueError):
            EnvironmentDict.from_yaml_dict({'key': ['list']})

    def test_to_yaml_dict_success_plain(self):
        obj = EnvironmentDict(foo='bar')
        assert obj.to_yaml_dict() == {'foo': 'bar'}

    def test_to_yaml_dict_success_to_encrypt(self):
        obj = EnvironmentDict(foo=ToEncrypt('bar'))
        assert obj.to_yaml_dict() == {'foo': {'to_encrypt': 'bar'}}

    def test_to_yaml_dict_success_encrypted(self):
        obj = EnvironmentDict(foo=Encrypted('bar'))
        assert obj.to_yaml_dict() == {'foo': {'encrypted': 'bar'}}

    def test_to_yaml_dict_fail_unknown_type(self):
        with pytest.raises(ValueError):
            EnvironmentDict(foo=1).to_yaml_dict()

    def test_decrypt_all_encrypted(self, kms_stub):
        obj = EnvironmentDict(
            TREEHUGGER_APP='foo',
            TREEHUGGER_STAGE='bar',
            baz=Encrypted(base64.b64encode(b'qux').decode('utf-8')),
            corge=ToEncrypt('grault'),
        )
        kms_stub.add_response(
            'decrypt',
            expected_params={
                'CiphertextBlob': b'qux',
                'EncryptionContext': {
                    'treehugger_app': 'foo',
                    'treehugger_key': 'baz',
                    'treehugger_stage': 'bar',
                }
            },
            service_response={
                'KeyId': 'treehugger',
                'Plaintext': b'quux',
            }
        )
        assert obj.decrypt_all_encrypted() == EnvironmentDict(
            TREEHUGGER_APP='foo',
            TREEHUGGER_STAGE='bar',
            baz=ToEncrypt('quux'),
            corge=ToEncrypt('grault'),
        )

    def test_decrypt_all_encrypted_plain(self, kms_stub):
        obj = EnvironmentDict(
            TREEHUGGER_APP='foo',
            TREEHUGGER_STAGE='bar',
            baz=Encrypted(base64.b64encode(b'qux').decode('utf-8')),
            corge=ToEncrypt('grault'),
        )
        kms_stub.add_response(
            'decrypt',
            expected_params={
                'CiphertextBlob': b'qux',
                'EncryptionContext': {
                    'treehugger_app': 'foo',
                    'treehugger_key': 'baz',
                    'treehugger_stage': 'bar',
                }
            },
            service_response={
                'KeyId': 'treehugger',
                'Plaintext': b'quux',
            }
        )
        assert obj.decrypt_all_encrypted(plain=True) == EnvironmentDict(
            TREEHUGGER_APP='foo',
            TREEHUGGER_STAGE='bar',
            baz='quux',
            corge='grault',
        )

    def test_encrypt_all_to_encrypt(self, kms_stub):
        obj = EnvironmentDict(
            TREEHUGGER_APP='foo',
            TREEHUGGER_STAGE='bar',
            baz=ToEncrypt('qux'),
        )
        kms_stub.add_response(
            'encrypt',
            expected_params={
                'KeyId': 'alias/treehugger',
                'Plaintext': b'qux',
                'EncryptionContext': {
                    'treehugger_app': 'foo',
                    'treehugger_key': 'baz',
                    'treehugger_stage': 'bar',
                }
            },
            service_response={
                'KeyId': 'treehugger',
                'CiphertextBlob': b'quux',
            }
        )
        assert obj.encrypt_all_to_encrypt() == EnvironmentDict(
            TREEHUGGER_APP='foo',
            TREEHUGGER_STAGE='bar',
            baz=Encrypted(base64.b64encode(b'quux').decode('utf-8')),
        )

    def test_remove_all_encrypted(self):
        obj = EnvironmentDict(
            TREEHUGGER_APP='foo',
            TREEHUGGER_STAGE='bar',
            baz=ToEncrypt('qux'),
            corge=Encrypted('grault'),
        )
        assert obj.remove_all_encrypted() == EnvironmentDict(
            TREEHUGGER_APP='foo',
            TREEHUGGER_STAGE='bar',
            baz=ToEncrypt('qux'),
        )

    def test_remove_all_encrypted_plain(self):
        obj = EnvironmentDict(
            TREEHUGGER_APP='foo',
            TREEHUGGER_STAGE='bar',
            baz=ToEncrypt('qux'),
            corge=Encrypted('grault'),
        )
        assert obj.remove_all_encrypted(plain=True) == EnvironmentDict(
            TREEHUGGER_APP='foo',
            TREEHUGGER_STAGE='bar',
            baz='qux',
        )
