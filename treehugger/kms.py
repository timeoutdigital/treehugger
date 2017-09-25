# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import base64

import boto3
from botocore.exceptions import NoRegionError

from .ec2 import get_current_region


class KMSAgent(object):

    key_id = 'alias/treehugger'

    def __init__(self):
        self.cache = {}

    def reset(self):
        self.cache = {}

    @property
    def kms_client(self):
        if not hasattr(self, '_kms_client'):
            try:
                self._kms_client = boto3.client('kms')
            except NoRegionError:
                region_name = get_current_region()
                self._kms_client = boto3.client('kms', region_name=region_name)
        return self._kms_client

    def decrypt(self, base64_ciphertext, encryption_context):
        cipher_blob = base64.b64decode(base64_ciphertext.encode('utf-8'))
        response = self.kms_client.decrypt(
            CiphertextBlob=cipher_blob,
            EncryptionContext=encryption_context,
        )
        plaintext = response['Plaintext'].decode('utf-8')
        cache_key = self._cache_key(plaintext, encryption_context)
        self.cache[cache_key] = base64_ciphertext
        return plaintext

    def encrypt(self, plaintext, encryption_context):
        cache_key = self._cache_key(plaintext, encryption_context)
        try:
            return self.cache[cache_key]
        except KeyError:
            pass

        response = self.kms_client.encrypt(
            KeyId=self.key_id,
            Plaintext=plaintext.encode('utf-8'),
            EncryptionContext=encryption_context
        )
        base64_ciphertext = base64.b64encode(response['CiphertextBlob']).decode('utf-8')
        self.cache[cache_key] = base64_ciphertext
        return base64_ciphertext

    def _cache_key(self, plaintext, encryption_context):
        return (plaintext,) + tuple(sorted(encryption_context.items()))


kms_agent = KMSAgent()
