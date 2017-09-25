# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import base64

import six

from treehugger.kms import kms_agent


class TestKMSAgent:

    def test_decrypt(self, kms_stub):
        context = {'foo': 'bar'}
        kms_stub.add_response(
            'decrypt',
            expected_params={
                'CiphertextBlob': b'baz',
                'EncryptionContext': context
            },
            service_response={
                'KeyId': 'treehugger',
                'Plaintext': b'qux',
            }
        )
        ciphertext_blob = base64.b64encode(b'baz').decode('utf-8')

        plaintext = kms_agent.decrypt(ciphertext_blob, context)

        assert plaintext == 'qux'

    def test_encrypt(self, kms_stub):
        context = {'foo': 'bar'}
        kms_stub.add_response(
            'encrypt',
            expected_params={
                'KeyId': 'alias/treehugger',
                'Plaintext': b'baz',
                'EncryptionContext': context
            },
            service_response={
                'KeyId': 'treehugger',
                'CiphertextBlob': b'qux',
            }
        )

        ciphertext_blob = kms_agent.encrypt('baz', context)

        assert isinstance(ciphertext_blob, six.text_type)
        assert ciphertext_blob == base64.b64encode(b'qux').decode('utf-8')

    def test_decrypt_encrypt_cached(self, kms_stub):
        context = {'foo': 'bar'}
        kms_stub.add_response(
            'decrypt',
            expected_params={
                'CiphertextBlob': b'baz',
                'EncryptionContext': context
            },
            service_response={
                'KeyId': 'treehugger',
                'Plaintext': b'qux',
            }
        )
        ciphertext_blob = base64.b64encode(b'baz').decode('utf-8')

        plaintext = kms_agent.decrypt(ciphertext_blob, context)
        ciphertext_blob2 = kms_agent.encrypt(plaintext, context)

        assert isinstance(ciphertext_blob2, six.text_type)
        assert ciphertext_blob2 == base64.b64encode(b'baz').decode('utf-8')

    def test_encrypt_encrypt_cached(self, kms_stub):
        context = {'foo': 'bar'}
        kms_stub.add_response(
            'encrypt',
            expected_params={
                'KeyId': 'alias/treehugger',
                'Plaintext': b'baz',
                'EncryptionContext': context
            },
            service_response={
                'KeyId': 'treehugger',
                'CiphertextBlob': b'qux',
            }
        )

        kms_agent.encrypt('baz', context)
        ciphertext_blob = kms_agent.encrypt('baz', context)

        assert isinstance(ciphertext_blob, six.text_type)
        assert ciphertext_blob == base64.b64encode(b'qux').decode('utf-8')

    def test_decrypt_encrypt_context_change_no_cache(self, kms_stub):
        context = {'foo': 'bar'}
        context2 = {'foo': 'bar2'}
        kms_stub.add_response(
            'decrypt',
            expected_params={
                'CiphertextBlob': b'baz',
                'EncryptionContext': context
            },
            service_response={
                'KeyId': 'treehugger',
                'Plaintext': b'qux',
            }
        )
        kms_stub.add_response(
            'encrypt',
            expected_params={
                'KeyId': 'alias/treehugger',
                'Plaintext': b'qux',
                'EncryptionContext': context2,
            },
            service_response={
                'KeyId': 'treehugger',
                'CiphertextBlob': b'quux',
            }
        )
        ciphertext_blob = base64.b64encode(b'baz').decode('utf-8')

        plaintext = kms_agent.decrypt(ciphertext_blob, context)
        ciphertext_blob2 = kms_agent.encrypt(plaintext, context2)

        assert isinstance(ciphertext_blob2, six.text_type)
        assert ciphertext_blob2 == base64.b64encode(b'quux').decode('utf-8')
