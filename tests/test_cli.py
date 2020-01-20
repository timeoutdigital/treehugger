import base64
import io
import json
import os
import textwrap
from unittest import mock

import pytest
import yaml

from treehugger import __version__
from treehugger.cli import main
from treehugger.ec2 import USER_DATA_URL


def test_help(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(['-h'])

    assert excinfo.value.code == 0
    out, err = capsys.readouterr()
    assert __version__ in out


def test_encrypt(tmpdir, kms_stub):
    tmpfile = tmpdir.join('test.yml')
    tmpfile.write(textwrap.dedent('''\
        MY_ENCRYPTED_VAR:
          to_encrypt: foo
        MY_UNENCRYPTED_VAR: bar
        TREEHUGGER_APP: baz
        TREEHUGGER_STAGE: qux
    '''))
    kms_stub.add_response(
        'encrypt',
        expected_params={
            'KeyId': 'alias/treehugger',
            'Plaintext': b'foo',
            'EncryptionContext': {
                'treehugger_app': 'baz',
                'treehugger_key': 'MY_ENCRYPTED_VAR',
                'treehugger_stage': 'qux',
            }
        },
        service_response={
            'KeyId': 'treehugger',
            'CiphertextBlob': b'quux',
        }
    )

    main(['encrypt-file', str(tmpfile)])

    data = yaml.safe_load(tmpfile.read())
    assert data['MY_ENCRYPTED_VAR'] == {'encrypted': base64.b64encode(b'quux').decode('utf-8')}
    assert data['MY_UNENCRYPTED_VAR'] == 'bar'
    assert data['TREEHUGGER_APP'] == 'baz'
    assert data['TREEHUGGER_STAGE'] == 'qux'


def test_encrypt_different_key(tmpdir, kms_stub):
    key_arn = 'arn:aws:kms:eu-west-1:123456789012:alias/treehugger'
    tmpfile = tmpdir.join('test.yml')
    tmpfile.write(textwrap.dedent('''\
        MY_ENCRYPTED_VAR:
          to_encrypt: foo
        MY_UNENCRYPTED_VAR: bar
        TREEHUGGER_APP: baz
        TREEHUGGER_STAGE: qux
    '''))
    kms_stub.add_response(
        'encrypt',
        expected_params={
            'KeyId': key_arn,
            'Plaintext': b'foo',
            'EncryptionContext': {
                'treehugger_app': 'baz',
                'treehugger_key': 'MY_ENCRYPTED_VAR',
                'treehugger_stage': 'qux',
            }
        },
        service_response={
            'KeyId': 'treehugger',
            'CiphertextBlob': b'quux',
        }
    )

    main(['-k', key_arn, 'encrypt-file', str(tmpfile)])

    data = yaml.safe_load(tmpfile.read())
    assert data['MY_ENCRYPTED_VAR'] == {'encrypted': base64.b64encode(b'quux').decode('utf-8')}
    assert data['MY_UNENCRYPTED_VAR'] == 'bar'
    assert data['TREEHUGGER_APP'] == 'baz'
    assert data['TREEHUGGER_STAGE'] == 'qux'


def test_encrypt_different_key_env_var(tmpdir, kms_stub):
    key_id = '3ab83b21-962e-2121-98b5-072cc2f296f1'
    tmpfile = tmpdir.join('test.yml')
    tmpfile.write(textwrap.dedent('''\
        MY_ENCRYPTED_VAR:
          to_encrypt: foo
        MY_UNENCRYPTED_VAR: bar
        TREEHUGGER_APP: baz
        TREEHUGGER_STAGE: qux
    '''))
    kms_stub.add_response(
        'encrypt',
        expected_params={
            'KeyId': key_id,
            'Plaintext': b'foo',
            'EncryptionContext': {
                'treehugger_app': 'baz',
                'treehugger_key': 'MY_ENCRYPTED_VAR',
                'treehugger_stage': 'qux',
            }
        },
        service_response={
            'KeyId': 'treehugger',
            'CiphertextBlob': b'quux',
        }
    )

    with mock.patch.dict(os.environ, {'TREEHUGGER_KEY': key_id}):
        main(['encrypt-file', str(tmpfile)])

    data = yaml.safe_load(tmpfile.read())
    assert data['MY_ENCRYPTED_VAR'] == {'encrypted': base64.b64encode(b'quux').decode('utf-8')}
    assert data['MY_UNENCRYPTED_VAR'] == 'bar'
    assert data['TREEHUGGER_APP'] == 'baz'
    assert data['TREEHUGGER_STAGE'] == 'qux'


def test_decrypt(tmpdir, kms_stub):
    tmpfile = tmpdir.join('test.yml')
    encrypted_var = base64.b64encode(b'foo')
    tmpfile.write(textwrap.dedent('''\
        MY_ENCRYPTED_VAR:
          encrypted: {encrypted_var}
        MY_UNENCRYPTED_VAR: bar
        TREEHUGGER_APP: baz
        TREEHUGGER_STAGE: qux
    '''.format(encrypted_var=encrypted_var.decode('utf-8'))))
    kms_stub.add_response(
        'decrypt',
        expected_params={
            'CiphertextBlob': b'foo',
            'EncryptionContext': {
                'treehugger_app': 'baz',
                'treehugger_key': 'MY_ENCRYPTED_VAR',
                'treehugger_stage': 'qux',
            }
        },
        service_response={
            'KeyId': 'treehugger',
            'Plaintext': b'quux',
        }
    )

    main(['decrypt-file', str(tmpfile)])

    data = yaml.safe_load(tmpfile.read())
    assert data['MY_ENCRYPTED_VAR'] == {'to_encrypt': 'quux'}
    assert data['MY_UNENCRYPTED_VAR'] == 'bar'
    assert data['TREEHUGGER_APP'] == 'baz'
    assert data['TREEHUGGER_STAGE'] == 'qux'


def test_edit(tmpdir, kms_stub):
    tmpfile = tmpdir.join('test.yml')
    encrypted_var = base64.b64encode(b'foo')
    tmpfile.write(textwrap.dedent('''\
        MY_ENCRYPTED_VAR:
          encrypted: {encrypted_var}
        MY_UNENCRYPTED_VAR: bar
        TREEHUGGER_APP: baz
        TREEHUGGER_STAGE: qux
    '''.format(encrypted_var=encrypted_var.decode('utf-8'))))
    kms_stub.add_response(
        'decrypt',
        expected_params={
            'CiphertextBlob': b'foo',
            'EncryptionContext': {
                'treehugger_app': 'baz',
                'treehugger_key': 'MY_ENCRYPTED_VAR',
                'treehugger_stage': 'qux',
            }
        },
        service_response={
            'KeyId': 'treehugger',
            'Plaintext': b'quux',
        }
    )

    def fake_call(command):
        assert len(command) == 2
        assert command[0] == 'nano'
        filename = command[1]
        with open(filename, 'r') as fp:
            obj = yaml.safe_load(fp.read())
        assert obj == {
            'MY_ENCRYPTED_VAR': {'to_encrypt': 'quux'},
            'MY_UNENCRYPTED_VAR': 'bar',
            'TREEHUGGER_APP': 'baz',
            'TREEHUGGER_STAGE': 'qux',
        }

        with open(filename, 'w') as fp:
            fp.write(textwrap.dedent('''\
                MY_ENCRYPTED_VAR: {to_encrypt: quux2}
                MY_UNENCRYPTED_VAR: bar
                TREEHUGGER_APP: baz
                TREEHUGGER_STAGE: qux
            '''))
        return 0

    kms_stub.add_response(
        'encrypt',
        expected_params={
            'KeyId': 'alias/treehugger',
            'Plaintext': b'quux2',
            'EncryptionContext': {
                'treehugger_app': 'baz',
                'treehugger_key': 'MY_ENCRYPTED_VAR',
                'treehugger_stage': 'qux',
            }
        },
        service_response={
            'KeyId': 'treehugger',
            'CiphertextBlob': b'foo',
        }
    )
    with mock.patch.dict(os.environ, {'EDITOR': 'nano'}), mock.patch('subprocess.call', new=fake_call):
        main(['edit', str(tmpfile)])


def test_edit_no_change(tmpdir, kms_stub):
    tmpfile = tmpdir.join('test.yml')
    encrypted_var = base64.b64encode(b'foo')
    tmpfile.write(textwrap.dedent('''\
        MY_ENCRYPTED_VAR:
          encrypted: {encrypted_var}
        MY_UNENCRYPTED_VAR: bar
        TREEHUGGER_APP: baz
        TREEHUGGER_STAGE: qux
    '''.format(encrypted_var=encrypted_var.decode('utf-8'))))
    kms_stub.add_response(
        'decrypt',
        expected_params={
            'CiphertextBlob': b'foo',
            'EncryptionContext': {
                'treehugger_app': 'baz',
                'treehugger_key': 'MY_ENCRYPTED_VAR',
                'treehugger_stage': 'qux',
            }
        },
        service_response={
            'KeyId': 'treehugger',
            'Plaintext': b'quux',
        }
    )

    with mock.patch.dict(os.environ, {'EDITOR': 'nano'}), mock.patch('subprocess.call') as mock_call:
        mock_call.return_value = 0
        main(['edit', str(tmpfile)])

    editor_args = mock_call.mock_calls[0][1][0]
    assert len(editor_args) == 2
    assert editor_args[0] == 'nano'
    assert editor_args[1].endswith('.yml')  # temp filename


def test_exec(requests_mock, kms_stub, capsys):
    encrypted_var = base64.b64encode(b'foo')
    requests_mock.get(
        USER_DATA_URL,
        text=textwrap.dedent('''\
            treehugger:
                MY_ENCRYPTED_VAR:
                  encrypted: {encrypted_var}
                MY_UNENCRYPTED_VAR: bar
                TREEHUGGER_APP: baz
                TREEHUGGER_STAGE: qux
        '''.format(encrypted_var=encrypted_var.decode('utf-8'))),
        status_code=200,
    )
    kms_stub.add_response(
        'decrypt',
        expected_params={
            'CiphertextBlob': b'foo',
            'EncryptionContext': {
                'treehugger_app': 'baz',
                'treehugger_key': 'MY_ENCRYPTED_VAR',
                'treehugger_stage': 'qux',
            }
        },
        service_response={
            'KeyId': 'treehugger',
            'Plaintext': b'quux',
        }
    )

    with mock.patch('os.execlp') as mock_execlp, mock.patch('os.environ', new={}) as mock_environ:
        main(['exec', '--', 'env'])

    mock_execlp.assert_called_with('env', 'env')
    assert mock_environ == {
        'MY_ENCRYPTED_VAR': 'quux',
        'MY_UNENCRYPTED_VAR': 'bar',
        'TREEHUGGER_APP': 'baz',
        'TREEHUGGER_STAGE': 'qux',
    }


def test_exec_with_ignore_missing(requests_mock, kms_stub, capsys):
    requests_mock.get(USER_DATA_URL, status_code=404)

    with mock.patch('os.execlp') as mock_execlp, mock.patch('os.environ', new={}) as mock_environ:
        main(['exec', '--ignore-missing', '--', 'env'])

    mock_execlp.assert_called_with('env', 'env')
    assert mock_environ == {
        'TREEHUGGER_APP': 'Missing',
        'TREEHUGGER_STAGE': 'Missing',
    }


def test_exec_file(tmpdir, kms_stub):
    tmpfile = tmpdir.join('test.yml')
    encrypted_var = base64.b64encode(b'foo')
    tmpfile.write(textwrap.dedent('''\
        MY_ENCRYPTED_VAR:
          encrypted: {encrypted_var}
        MY_UNENCRYPTED_VAR: bar
        TREEHUGGER_APP: baz
        TREEHUGGER_STAGE: qux
    '''.format(encrypted_var=encrypted_var.decode('utf-8'))))
    kms_stub.add_response(
        'decrypt',
        expected_params={
            'CiphertextBlob': b'foo',
            'EncryptionContext': {
                'treehugger_app': 'baz',
                'treehugger_key': 'MY_ENCRYPTED_VAR',
                'treehugger_stage': 'qux',
            }
        },
        service_response={
            'KeyId': 'treehugger',
            'Plaintext': b'quux',
        }
    )

    with mock.patch('os.execlp') as mock_execlp, mock.patch('os.environ', new={}) as mock_environ:
        main(['exec', '-f', str(tmpfile), '--', 'env'])

    mock_execlp.assert_called_with('env', 'env')
    assert mock_environ == {
        'MY_ENCRYPTED_VAR': 'quux',
        'MY_UNENCRYPTED_VAR': 'bar',
        'TREEHUGGER_APP': 'baz',
        'TREEHUGGER_STAGE': 'qux',
    }


def test_exec_no_command(tmpdir, capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(['exec'])

    assert excinfo.value.code == 1
    out, err = capsys.readouterr()
    assert 'No command to execute provided' in err


def test_exec_no_command_but_dashes(tmpdir, capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(['exec', '--'])

    assert excinfo.value.code == 1
    out, err = capsys.readouterr()
    assert 'No command to execute provided' in err


def test_print(requests_mock, kms_stub, capsys):
    encrypted_var = base64.b64encode(b'foo')
    requests_mock.get(
        USER_DATA_URL,
        text=textwrap.dedent('''\
            treehugger:
                MY_ENCRYPTED_VAR:
                  encrypted: {encrypted_var}
                MY_UNENCRYPTED_VAR: bar
                TREEHUGGER_APP: baz
                TREEHUGGER_STAGE: qux
        '''.format(encrypted_var=encrypted_var.decode('utf-8'))),
        status_code=200,
    )
    kms_stub.add_response(
        'decrypt',
        expected_params={
            'CiphertextBlob': b'foo',
            'EncryptionContext': {
                'treehugger_app': 'baz',
                'treehugger_key': 'MY_ENCRYPTED_VAR',
                'treehugger_stage': 'qux',
            }
        },
        service_response={
            'KeyId': 'treehugger',
            'Plaintext': b'quux',
        }
    )

    main(['print'])
    out, err = capsys.readouterr()

    out_lines = out.split('\n')

    assert out_lines == [
        'MY_ENCRYPTED_VAR=quux',
        'MY_UNENCRYPTED_VAR=bar',
        'TREEHUGGER_APP=baz',
        'TREEHUGGER_STAGE=qux',
        '',
    ]


def test_print_file(tmpdir, kms_stub, capsys):
    tmpfile = tmpdir.join('test.yml')
    encrypted_var = base64.b64encode(b'foo')
    tmpfile.write(textwrap.dedent('''\
        MY_ENCRYPTED_VAR:
          encrypted: {encrypted_var}
        MY_UNENCRYPTED_VAR: bar
        TREEHUGGER_APP: baz
        TREEHUGGER_STAGE: qux
    '''.format(encrypted_var=encrypted_var.decode('utf-8'))))
    kms_stub.add_response(
        'decrypt',
        expected_params={
            'CiphertextBlob': b'foo',
            'EncryptionContext': {
                'treehugger_app': 'baz',
                'treehugger_key': 'MY_ENCRYPTED_VAR',
                'treehugger_stage': 'qux',
            }
        },
        service_response={
            'KeyId': 'treehugger',
            'Plaintext': b'quux',
        }
    )

    main(['print', '-f', str(tmpfile)])
    out, err = capsys.readouterr()

    out_lines = out.split('\n')

    assert out_lines == [
        'MY_ENCRYPTED_VAR=quux',
        'MY_UNENCRYPTED_VAR=bar',
        'TREEHUGGER_APP=baz',
        'TREEHUGGER_STAGE=qux',
        '',
    ]


def test_print_file_with_include(tmpdir, kms_stub, s3_stub, capsys):
    tmpfile = tmpdir.join('test.yml')
    encrypted_var = base64.b64encode(b'foo')
    tmpfile.write(textwrap.dedent('''\
        include: s3://my-bucket/my_file.yml?versionId=2
        MY_ENCRYPTED_VAR:
          encrypted: {encrypted_var}
        MY_UNENCRYPTED_VAR: bar
        TREEHUGGER_APP: baz
        TREEHUGGER_STAGE: qux
    '''.format(encrypted_var=encrypted_var.decode('utf-8'))))
    kms_stub.add_response(
        'decrypt',
        expected_params={
            'CiphertextBlob': b'foo',
            'EncryptionContext': {
                'treehugger_app': 'baz',
                'treehugger_key': 'MY_ENCRYPTED_VAR',
                'treehugger_stage': 'qux',
            }
        },
        service_response={
            'KeyId': 'treehugger',
            'Plaintext': b'quux',
        }
    )
    s3_stub.add_response(
        'get_object',
        expected_params={
            'Bucket': 'my-bucket',
            'Key': 'my_file.yml',
            'VersionId': '2',
        },
        service_response={
            'Body': io.BytesIO(b'MY_INCLUDED_VAR: IliveinS3'),
        }
    )

    main(['print', '-f', str(tmpfile)])
    out, err = capsys.readouterr()

    out_lines = out.split('\n')

    assert out_lines == [
        'MY_ENCRYPTED_VAR=quux',
        'MY_INCLUDED_VAR=IliveinS3',
        'MY_UNENCRYPTED_VAR=bar',
        'TREEHUGGER_APP=baz',
        'TREEHUGGER_STAGE=qux',
        '',
    ]


def test_print_env_s3(kms_stub, s3_stub, capsys):
    encrypted_var = base64.b64encode(b'foo')
    os.environ['TREEHUGGER_DATA'] = 's3://my-bucket/my_file.yml?versionId=2'
    response = textwrap.dedent('''\
                        MY_ENCRYPTED_VAR:
                          encrypted: {encrypted_var}
                        MY_UNENCRYPTED_VAR: bar
                        TREEHUGGER_APP: baz
                        TREEHUGGER_STAGE: qux
                        '''.format(encrypted_var=encrypted_var.decode('utf-8'))).encode()
    s3_stub.add_response(
        'get_object',
        expected_params={
            'Bucket': 'my-bucket',
            'Key': 'my_file.yml',
            'VersionId': '2',
        },
        service_response={
            'Body': io.BytesIO(response)
        }
    )
    kms_stub.add_response(
        'decrypt',
        expected_params={
            'CiphertextBlob': b'foo',
            'EncryptionContext': {
                'treehugger_app': 'baz',
                'treehugger_key': 'MY_ENCRYPTED_VAR',
                'treehugger_stage': 'qux',
            }
        },
        service_response={
            'KeyId': 'treehugger',
            'Plaintext': b'quux',
        }
    )

    main(['print'])
    out, err = capsys.readouterr()
    print('----------', out)
    out_lines = out.split('\n')
    assert out_lines == [
        'MY_ENCRYPTED_VAR=quux',
        'MY_UNENCRYPTED_VAR=bar',
        'TREEHUGGER_APP=baz',
        'TREEHUGGER_STAGE=qux',
        '',
    ]
    del os.environ['TREEHUGGER_DATA']


def test_print_no_var_with_quote(tmpdir, capsys):
    tmpfile = tmpdir.join('test.yml')
    tmpfile.write(textwrap.dedent('''\
        MY_UNENCRYPTED_VAR: 'my var with "quotes"'
        TREEHUGGER_APP: baz
        TREEHUGGER_STAGE: qux
    '''))

    main(['print', '-f', str(tmpfile)])
    out, err = capsys.readouterr()

    out_lines = out.split('\n')

    assert out_lines == [
        'MY_UNENCRYPTED_VAR=\'my var with "quotes"\'',
        'TREEHUGGER_APP=baz',
        'TREEHUGGER_STAGE=qux',
        '',
    ]


def test_print_only_unencrypted(tmpdir, capsys):
    tmpfile = tmpdir.join('test.yml')
    tmpfile.write(textwrap.dedent('''\
        MY_ENCRYPTED_VAR:
          encrypted: IGNOREME
        MY_UNENCRYPTED_VAR: bar
        TREEHUGGER_APP: baz
        TREEHUGGER_STAGE: qux
    '''))

    main(['print', '-f', str(tmpfile), '--only-unencrypted'])
    out, err = capsys.readouterr()

    out_lines = out.split('\n')

    assert out_lines == [
        'MY_UNENCRYPTED_VAR=bar',
        'TREEHUGGER_APP=baz',
        'TREEHUGGER_STAGE=qux',
        '',
    ]


def test_print_single_line(tmpdir, capsys):
    tmpfile = tmpdir.join('test.yml')
    tmpfile.write(textwrap.dedent('''\
        MY_UNENCRYPTED_VAR: bar
        TREEHUGGER_APP: baz
        TREEHUGGER_STAGE: qux
    '''))

    main(['print', '-f', str(tmpfile), '--single-line'])
    out, err = capsys.readouterr()

    assert out == 'MY_UNENCRYPTED_VAR=bar TREEHUGGER_APP=baz TREEHUGGER_STAGE=qux\n'


def test_print_json(tmpdir, capsys):
    tmpfile = tmpdir.join('test.yml')
    tmpfile.write(textwrap.dedent('''\
        MY_UNENCRYPTED_VAR: bar
        TREEHUGGER_APP: baz
        TREEHUGGER_STAGE: qux
    '''))

    main(['print', '-f', str(tmpfile), '--json'])
    out, err = capsys.readouterr()

    assert out.count('\n') == 5
    assert json.loads(out) == {
        "MY_UNENCRYPTED_VAR": "bar",
        "TREEHUGGER_APP": "baz",
        "TREEHUGGER_STAGE": "qux"
    }


def test_print_json_single_line(tmpdir, capsys):
    tmpfile = tmpdir.join('test.yml')
    tmpfile.write(textwrap.dedent('''\
        MY_UNENCRYPTED_VAR: bar
        TREEHUGGER_APP: baz
        TREEHUGGER_STAGE: qux
    '''))

    main(['print', '-f', str(tmpfile), '--json', '--single-line'])
    out, err = capsys.readouterr()

    assert out.count('\n') == 1
    assert json.loads(out) == {
        "MY_UNENCRYPTED_VAR": "bar",
        "TREEHUGGER_APP": "baz",
        "TREEHUGGER_STAGE": "qux"
    }
