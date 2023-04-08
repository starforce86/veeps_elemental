import uuid

from botocore import session
from botocore.stub import Stubber


@staticmethod
def mock_get_boto_client(resource_name):
    client = session.get_session().create_client(resource_name)

    stubber = Stubber(client)

    stubber.activate()
    return client


# noinspection PyUnusedLocal
def mock_create_stack(self, region=None):
    return {"StackId": f"{uuid.uuid4()}"}


# noinspection PyUnusedLocal
def mock_delete_stack(self):
    return {"StackId": f"{uuid.uuid4()}"}


# noinspection PyUnusedLocal
def mock_get_outputs(self):
    return [
        {
            "OutputKey": "ChannelArn",
            "OutputValue": "1234",
        }
    ]


# noinspection PyUnusedLocal
def mock_none(self):
    return
