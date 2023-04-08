import logging

from django.urls import reverse
from rest_framework import status

from . import VeepsTestCase
from .factories import (
    PlayoutFactory,
    ChannelFactory,
    InputFactory,
    DistributionFactory,
)

logger = logging.getLogger(__name__)


class DistributionTests(VeepsTestCase):
    databases = "__all__"
    playout = None
    get_distribution_res = None
    update_distribution_res = None
    delete_distribution_res = None

    def tearDown(self) -> None:
        pass

    @classmethod
    def tearDownClass(cls) -> None:
        pass

    def setUp(self):
        super().setUp()

        self.playout = PlayoutFactory()
        channel = ChannelFactory()
        channel.save()
        self.playout.channel = channel

        distribution = DistributionFactory(
            name="test",
            description="test description",
            hls_url="http://test.test",
        )
        distribution.save()

        self.playout.distribution = distribution
        self.playout.save()

        input = InputFactory()
        input.playout = self.playout
        input.save()

        self.distribution_data = {
            "name": "distribution_name",
            "description": "distribution_description",
            "hls_url": "hls_url",
            "price_class": "price_class",
            "mediapackage_id": "cfee63c6-b071-4389-a040-9db2f17ef278",
            "cloudfront_id": "90399",
            "cloudformation_template": "59943",
        }
        self.distribution_new_data = {
            "name": "distribution_name_new",
            "description": "distribution_description_new",
            "hls_url": "hls_url_new",
            "price_class": "price_class_new",
            "mediapackage_id": "d1ce0102-caf8-42ee-8012-68a42c6157c2",
            "cloudfront_id": "10399",
            "cloudformation_template": "19943",
        }
        self.playout_data = {"resolution": "HD"}

    def test_distribution(self):
        endpoint_url = reverse("distribution-detail", kwargs={"playout_id": self.playout.id})
        logging.info("======> Get Distribution of Playout API (GET {})".format(endpoint_url))

        get_distribution_res = self.client.get(endpoint_url, format="json")

        logging.info("=========> should return status code 200")
        self.assertEqual(get_distribution_res.status_code, status.HTTP_200_OK)

        logging.info("=========> should make sure that each fields of response are valid")

        get_data = get_distribution_res.json()

        self.assertEquals(get_data["hls_url"], "http://test.test")
