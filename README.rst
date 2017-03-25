Treehugger
==========

.. image:: https://travis-ci.org/timeoutdigital/treehugger.svg?branch=master
    :target: https://travis-ci.org/timeoutdigital/treehugger

Takes care of your environment (variables) on AWS.

Requirements
------------

* Python 2.7+ or 3.4+
* Some simple dependencies as listed in ``setup.py`` - ``boto3``, ``PyYAML``,
  ``requests``, and ``six``.
* A KMS key in your account aliased as ``alias/treehugger``.

How it works
------------

Treehugger lets you use `KMS <https://aws.amazon.com/kms/>`_ encrypted environment variables to run your application on
EC2. You store the encrypted variables in YAML files alongside your other configuration management, then just get them
into the EC2 User Data for an instance. Treehugger can read the variables from user data, decrypt the encrypted ones,
and run your application.

For example, say we want to run an application that takes a ``GITHUB_TOKEN`` environment variable for talking to
GitHub. Since this is sensitive data, we want to store it encrypted and only decrypt it when running the application.
You can start by writing a YAML file `my_app_vars.yml` that contains the variable in its unencrypted form, in a
``to_encrypt`` key in a mapping that indicates it should be encrypted:

.. code-block:: yaml

    GITHUB_TOKEN: {to_encrypt: example-token}
    TREEHUGGER_APP: my-app
    TREEHUGGER_STAGE: prod

The ``TREEHUGGER_APP`` and ``TREEHUGGER_STAGE`` variables are mandatory and used to provide context to Treehugger. They
are used to encrypt the variables using KMS's `Encryption Context
<https://docs.aws.amazon.com/kms/latest/developerguide/encryption-context.html>`_ feature, giving access control and
protection against tampering.

You can encrypt the file by running:

.. code-block:: sh

    treehugger encrypt-file my_app_vars.yml

It'll be changed to something like:

.. code-block:: yaml

    GITHUB_TOKEN: {encrypted: AQECAHiVqEdWu6BhwWXkqJrEhgPpuDXA3TC1MPUeQb...}
    TREEHUGGER_APP: my-app
    TREEHUGGER_STAGE: prod

Note that the plaintext variables are not encrypted, only those marked ``to_encrypt``.

Going forwards you can edit the file with:

.. code-block:: sh

    treehugger edit my_app_vars.yml

This will decrypt the file into a temporary file, open that in your ``$EDITOR``, then once that finishes encrypt it
back in place. This avoids any risk of accidentally committing your decrypted secrets.

For deployment, it's up to you to get the contents of that file into the `User Data
<https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-metadata.html>`_ of the EC2 instance of the
application, underneath the key ``treehugger``.

For example, you could pass the contents of the file as a parameter to a CloudFormation template that puts the value
into the ``UserData`` property of an AutoScaling Group. For example if passed in as a parameter ``TreehuggerUserData``
(with extra indentation):

.. code-block:: yaml

    LaunchConfig:
      Type: AWS::AutoScaling::LaunchConfiguration
      Properties:
        UserData:
          Fn::Base64:
            !Sub
            - |
              treehugger:
                ${IndentedTreehuggerUserData}

Then on the EC2 instance your application can be started with:

.. code-block:: sh

    treehugger exec -- /path/to/application

Treehugger will load the User Data as YAML, extract the dictionary under the 'treehugger' key, decrypt the variables
marked ``encrypted``, put them into the environment, and then replace itself with a copy of the application using
`execlp <https://linux.die.net/man/3/execlp>`_.

Testing
-------

Install and run ``tox`` (`docs <https://tox.readthedocs.io/en/latest/>`_).

Credits
-------

Treehugger was created by `Niklas Lindblad <https://github.com/nlindblad>`_ and is now maintained by `Adam Johnson
<https://github.com/adamchainz>`_.
