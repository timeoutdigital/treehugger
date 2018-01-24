# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import base64
import io
import json
import os
import textwrap
from unittest import mock

import pytest
import responses
import six
import yaml

from treehugger import __version__
from treehugger.cli import main
from treehugger.ec2 import USER_DATA_URL


class TestCLI:

    def test_help(self, capsys):
        with pytest.raises(SystemExit) as excinfo:
            main(['-h'])

        assert excinfo.value.code == 0
        out, err = capsys.readouterr()
        assert __version__ in out

    def test_encrypt(self, tmpdir, kms_stub):
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

        main(['encrypt-file', six.text_type(tmpfile)])

        data = yaml.load(tmpfile.read())
        assert data['MY_ENCRYPTED_VAR'] == {'encrypted': base64.b64encode(b'quux').decode('utf-8')}
        assert data['MY_UNENCRYPTED_VAR'] == 'bar'
        assert data['TREEHUGGER_APP'] == 'baz'
        assert data['TREEHUGGER_STAGE'] == 'qux'

    def test_encrypt_different_key(self, tmpdir, kms_stub):
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

        main(['-k', key_arn, 'encrypt-file', six.text_type(tmpfile)])

        data = yaml.load(tmpfile.read())
        assert data['MY_ENCRYPTED_VAR'] == {'encrypted': base64.b64encode(b'quux').decode('utf-8')}
        assert data['MY_UNENCRYPTED_VAR'] == 'bar'
        assert data['TREEHUGGER_APP'] == 'baz'
        assert data['TREEHUGGER_STAGE'] == 'qux'

    def test_encrypt_different_key_env_var(self, tmpdir, kms_stub):
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
            main(['encrypt-file', six.text_type(tmpfile)])

        data = yaml.load(tmpfile.read())
        assert data['MY_ENCRYPTED_VAR'] == {'encrypted': base64.b64encode(b'quux').decode('utf-8')}
        assert data['MY_UNENCRYPTED_VAR'] == 'bar'
        assert data['TREEHUGGER_APP'] == 'baz'
        assert data['TREEHUGGER_STAGE'] == 'qux'

    def test_decrypt(self, tmpdir, kms_stub):
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

        main(['decrypt-file', six.text_type(tmpfile)])

        data = yaml.load(tmpfile.read())
        assert data['MY_ENCRYPTED_VAR'] == {'to_encrypt': 'quux'}
        assert data['MY_UNENCRYPTED_VAR'] == 'bar'
        assert data['TREEHUGGER_APP'] == 'baz'
        assert data['TREEHUGGER_STAGE'] == 'qux'

    def test_edit(self, tmpdir, kms_stub):
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
            main(['edit', six.text_type(tmpfile)])

    def test_edit_no_change(self, tmpdir, kms_stub):
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
            main(['edit', six.text_type(tmpfile)])

        editor_args = mock_call.mock_calls[0][1][0]
        assert len(editor_args) == 2
        assert editor_args[0] == 'nano'
        assert editor_args[1].endswith('.yml')  # temp filename

    @responses.activate
    def test_exec(self, kms_stub, capsys):
        encrypted_var = base64.b64encode(b'foo')
        responses.add(
            responses.GET,
            USER_DATA_URL,
            body=textwrap.dedent('''\
                treehugger:
                    MY_ENCRYPTED_VAR:
                      encrypted: {encrypted_var}
                    MY_UNENCRYPTED_VAR: bar
                    TREEHUGGER_APP: baz
                    TREEHUGGER_STAGE: qux
            '''.format(encrypted_var=encrypted_var.decode('utf-8'))),
            status=200,
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

    @responses.activate
    def test_exec_with_ignore_missing(self, kms_stub, capsys):
        responses.add(responses.GET, USER_DATA_URL, status=404)

        with mock.patch('os.execlp') as mock_execlp, mock.patch('os.environ', new={}) as mock_environ:
            main(['exec', '--ignore-missing', '--', 'env'])

        mock_execlp.assert_called_with('env', 'env')
        assert mock_environ == {
            'TREEHUGGER_APP': 'Missing',
            'TREEHUGGER_STAGE': 'Missing',
        }

    def test_exec_file(self, tmpdir, kms_stub):
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
            main(['exec', '-f', six.text_type(tmpfile), '--', 'env'])

        mock_execlp.assert_called_with('env', 'env')
        assert mock_environ == {
            'MY_ENCRYPTED_VAR': 'quux',
            'MY_UNENCRYPTED_VAR': 'bar',
            'TREEHUGGER_APP': 'baz',
            'TREEHUGGER_STAGE': 'qux',
        }

    def test_exec_no_command(self, tmpdir, capsys):
        with pytest.raises(SystemExit) as excinfo:
            main(['exec'])

        assert excinfo.value.code == 1
        out, err = capsys.readouterr()
        assert 'No command to execute provided' in err

    def test_exec_no_command_but_dashes(self, tmpdir, capsys):
        with pytest.raises(SystemExit) as excinfo:
            main(['exec', '--'])

        assert excinfo.value.code == 1
        out, err = capsys.readouterr()
        assert 'No command to execute provided' in err

    @responses.activate
    def test_print(self, kms_stub, capsys):
        encrypted_var = base64.b64encode(b'foo')
        responses.add(
            responses.GET,
            USER_DATA_URL,
            body=textwrap.dedent('''\
                treehugger:
                    MY_ENCRYPTED_VAR:
                      encrypted: {encrypted_var}
                    MY_UNENCRYPTED_VAR: bar
                    TREEHUGGER_APP: baz
                    TREEHUGGER_STAGE: qux
            '''.format(encrypted_var=encrypted_var.decode('utf-8'))),
            status=200,
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

    def test_print_file(self, tmpdir, kms_stub, capsys):
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

        main(['print', '-f', six.text_type(tmpfile)])
        out, err = capsys.readouterr()

        out_lines = out.split('\n')

        assert out_lines == [
            'MY_ENCRYPTED_VAR=quux',
            'MY_UNENCRYPTED_VAR=bar',
            'TREEHUGGER_APP=baz',
            'TREEHUGGER_STAGE=qux',
            '',
        ]

    def test_print_file_with_include(self, tmpdir, kms_stub, s3_stub, capsys):
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

        main(['print', '-f', six.text_type(tmpfile)])
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

    def test_print_no_var_with_quote(self, tmpdir, capsys):
        tmpfile = tmpdir.join('test.yml')
        tmpfile.write(textwrap.dedent('''\
            MY_UNENCRYPTED_VAR: 'my var with "quotes"'
            TREEHUGGER_APP: baz
            TREEHUGGER_STAGE: qux
        '''))

        main(['print', '-f', six.text_type(tmpfile)])
        out, err = capsys.readouterr()

        out_lines = out.split('\n')

        assert out_lines == [
            'MY_UNENCRYPTED_VAR=\'my var with "quotes"\'',
            'TREEHUGGER_APP=baz',
            'TREEHUGGER_STAGE=qux',
            '',
        ]

    def test_print_only_unencrypted(self, tmpdir, capsys):
        tmpfile = tmpdir.join('test.yml')
        tmpfile.write(textwrap.dedent('''\
            MY_ENCRYPTED_VAR:
              encrypted: IGNOREME
            MY_UNENCRYPTED_VAR: bar
            TREEHUGGER_APP: baz
            TREEHUGGER_STAGE: qux
        '''))

        main(['print', '-f', six.text_type(tmpfile), '--only-unencrypted'])
        out, err = capsys.readouterr()

        out_lines = out.split('\n')

        assert out_lines == [
            'MY_UNENCRYPTED_VAR=bar',
            'TREEHUGGER_APP=baz',
            'TREEHUGGER_STAGE=qux',
            '',
        ]

    def test_print_single_line(self, tmpdir, capsys):
        tmpfile = tmpdir.join('test.yml')
        tmpfile.write(textwrap.dedent('''\
            MY_UNENCRYPTED_VAR: bar
            TREEHUGGER_APP: baz
            TREEHUGGER_STAGE: qux
        '''))

        main(['print', '-f', six.text_type(tmpfile), '--single-line'])
        out, err = capsys.readouterr()

        assert out == 'MY_UNENCRYPTED_VAR=bar TREEHUGGER_APP=baz TREEHUGGER_STAGE=qux\n'

    def test_print_json(self, tmpdir, capsys):
        tmpfile = tmpdir.join('test.yml')
        tmpfile.write(textwrap.dedent('''\
            MY_UNENCRYPTED_VAR: bar
            TREEHUGGER_APP: baz
            TREEHUGGER_STAGE: qux
        '''))

        main(['print', '-f', six.text_type(tmpfile), '--json'])
        out, err = capsys.readouterr()

        assert out.count('\n') == 5
        assert json.loads(out) == {
            "MY_UNENCRYPTED_VAR": "bar",
            "TREEHUGGER_APP": "baz",
            "TREEHUGGER_STAGE": "qux"
        }

    def test_print_json_single_line(self, tmpdir, capsys):
        tmpfile = tmpdir.join('test.yml')
        tmpfile.write(textwrap.dedent('''\
            MY_UNENCRYPTED_VAR: bar
            TREEHUGGER_APP: baz
            TREEHUGGER_STAGE: qux
        '''))

        main(['print', '-f', six.text_type(tmpfile), '--json', '--single-line'])
        out, err = capsys.readouterr()

        assert out.count('\n') == 1
        assert json.loads(out) == {
            "MY_UNENCRYPTED_VAR": "bar",
            "TREEHUGGER_APP": "baz",
            "TREEHUGGER_STAGE": "qux"
        }
