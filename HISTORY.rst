.. :changelog:

=======
History
=======

Pending Release
---------------

* (Insert new release notes below this line)
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
