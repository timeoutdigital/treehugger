.. :changelog:

=======
History
=======

Pending Release
---------------

* (Insert new release notes below this line)

1.2.1 (2017-09-02)
------------------

* Fix a bug where cached values in 'edit' would be reused when changing the
  app, stage, or variable names, which change the KMS encryption context.

1.2.0 (2017-08-31)
------------------

* Add ``--json`` argument to ``print`` command.
* Make 'edit' reuse previous encrypted values that weren't changed.

1.1.0 (2017-04-05)
------------------

* Support using a different KMS key (ID, Alias, or ARN) for encryption from the
  ``-k``/``--key`` argument or the environment variable ``TREEHUGGER_KEY``.
  This is mostly useful for cross-account key sharing.

1.0.2 (2017-03-16)
------------------

* Fix ``KeyError`` when reading from EC2 User Data in 'exec'.

1.0.1 (2017-03-16)
------------------

* Fix ``KeyError`` when reading from EC2 User Data in 'print'.

1.0.0 (2017-03-14)
------------------

* Initial public version, featuring 'encrypt-file', 'decrypt-file', 'edit',
  'exec' and 'print' commands.
