# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import base64
import os
import textwrap
from unittest import mock

import pytest
import six
import yaml

from treehugger import __version__
from treehugger.cli import main


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
        assert list(data['MY_ENCRYPTED_VAR'].keys()) == ['encrypted']
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
        kms_stub.add_response(
            'encrypt',
            expected_params={
                'KeyId': 'alias/treehugger',
                'Plaintext': b'quux',
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

        with mock.patch.dict(os.environ, {'EDITOR': 'nano'}), mock.patch('subprocess.call') as mock_call:
            mock_call.return_value = 0
            main(['edit', six.text_type(tmpfile)])

        editor_args = mock_call.mock_calls[0][1][0]
        assert len(editor_args) == 2
        assert editor_args[0] == 'nano'
        assert editor_args[1].endswith('.yml')  # temp filename

    def test_exec(self, tmpdir, kms_stub):
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

    def test_print(self, tmpdir, kms_stub, capsys):
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
