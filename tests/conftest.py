# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import pytest
from botocore.stub import Stubber

from treehugger.kms import kms_agent


@pytest.fixture(scope='function', autouse=True)
def kms_stub():
    kms_agent.reset()
    with Stubber(kms_agent.kms_client) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()
