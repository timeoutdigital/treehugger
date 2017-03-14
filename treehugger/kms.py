# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import base64

import boto3
from botocore.exceptions import NoRegionError

from .ec2 import get_current_region


class KMSAgent(object):

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
        cipher_blob = base64.b64decode(base64_ciphertext)
        response = self.kms_client.decrypt(
            CiphertextBlob=cipher_blob,
            EncryptionContext=encryption_context,
        )
        return response['Plaintext'].decode('utf-8')

    def encrypt(self, plaintext, encryption_context):
        response = self.kms_client.encrypt(
            KeyId='alias/treehugger',
            Plaintext=plaintext.encode('utf-8'),
            EncryptionContext=encryption_context
        )
        base64_ciphertext = base64.b64encode(response['CiphertextBlob'])
        return base64_ciphertext


kms_agent = KMSAgent()
