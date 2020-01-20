import base64

from treehugger.kms import kms_agent


def test_decrypt(kms_stub):
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


def test_encrypt(kms_stub):
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

    assert isinstance(ciphertext_blob, str)
    assert ciphertext_blob == base64.b64encode(b'qux').decode('utf-8')


def test_decrypt_encrypt_cached(kms_stub):
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

    assert isinstance(ciphertext_blob2, str)
    assert ciphertext_blob2 == base64.b64encode(b'baz').decode('utf-8')


def test_encrypt_encrypt_cached(kms_stub):
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

    assert isinstance(ciphertext_blob, str)
    assert ciphertext_blob == base64.b64encode(b'qux').decode('utf-8')


def test_decrypt_encrypt_context_change_no_cache(kms_stub):
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

    assert isinstance(ciphertext_blob2, str)
    assert ciphertext_blob2 == base64.b64encode(b'quux').decode('utf-8')
