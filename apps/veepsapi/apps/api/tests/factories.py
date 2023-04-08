import factory

from rest_framework.authtoken.models import Token

from ..models import Playout, Input, Channel, Distribution

from apps.users.models import User


class TokenFactory(factory.Factory):
    class Meta:
        model = Token


class UserFactory(factory.Factory):
    class Meta:
        model = User

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.LazyAttribute(lambda o: f"{o.first_name}@test.com".lower())
    is_admin = False
    is_superuser = False
    is_staff = False

    auth_token = factory.SubFactory(TokenFactory)


class InputFactory(factory.Factory):
    class Meta:
        model = Input

    initial_input = True
    protocol = "srt"
    port = "2000"


class ChannelFactory(factory.Factory):
    class Meta:
        model = Channel


class DistributionFactory(factory.Factory):
    class Meta:
        model = Distribution

    name = "test"
    description = "test"
    hls_url = "http://test.test"


class PlayoutFactory(factory.Factory):
    class Meta:
        model = Playout

    resolution = "HD"
    channel = factory.RelatedFactory(ChannelFactory)
    input = factory.RelatedFactory(InputFactory)
