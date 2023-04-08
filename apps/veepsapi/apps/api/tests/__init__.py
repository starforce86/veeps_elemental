from django.test import SimpleTestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from ..cloudformation.liveinput import MediaLiveInputLive
from ..models import Playout, Input, Channel
from ..tests.factories import UserFactory
from ..cloudformation import CloudFormationStackGeneric
from ..tests.mocks import mock_delete_stack, mock_get_outputs, mock_get_boto_client, mock_none, mock_create_stack
from ..cloudformation.channel import MediaLiveChannel
from ..serializers import VeepsSerializer


class VeepsTestCase(SimpleTestCase):
    databases = "__all__"

    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory(is_superuser=True)
        self.user.save()

        # monkey patch the generic to bypass running cloudformation directly
        setattr(CloudFormationStackGeneric, "create", mock_create_stack)
        setattr(CloudFormationStackGeneric, "delete", mock_delete_stack)
        setattr(CloudFormationStackGeneric, "get_outputs", mock_get_outputs)
        setattr(CloudFormationStackGeneric, "get_boto_client", mock_get_boto_client)
        setattr(CloudFormationStackGeneric, "update_change_set", mock_none)
        setattr(MediaLiveChannel, "start", mock_none)
        setattr(MediaLiveChannel, "stop", mock_none)
        setattr(MediaLiveInputLive, "start", mock_none)
        setattr(MediaLiveInputLive, "stop", mock_none)
        setattr(VeepsSerializer, "get_boto_client", mock_get_boto_client)

        token = Token.objects.create(user=self.user)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        # clear anything that could interfere with the test
        for playout in Playout.objects.all():
            playout.delete()

        for inputs in Input.objects.all():
            inputs.delete()

        for channel in Channel.objects.all():
            channel.delete()
