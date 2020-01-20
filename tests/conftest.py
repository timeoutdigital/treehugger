import pytest
from botocore.stub import Stubber

from treehugger.kms import kms_agent
from treehugger.s3 import s3_client


@pytest.fixture(scope='function', autouse=True)
def kms_stub():
    kms_agent.reset()
    with Stubber(kms_agent.kms_client) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()


@pytest.fixture(scope='function', autouse=True)
def s3_stub():
    with Stubber(s3_client) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()
