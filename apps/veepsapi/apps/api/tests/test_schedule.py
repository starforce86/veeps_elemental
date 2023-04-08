import logging

from django.urls import reverse

from . import VeepsTestCase
from .factories import PlayoutFactory
from ..models import Playout

logger = logging.getLogger(__name__)


class ScheduleTests(VeepsTestCase):
    def setUp(self):
        super().setUp()
        self.playout_data = PlayoutFactory()
        self.playout_data.save()

    def test_schedule(self):
        logging.info("===> Testing Schedule APIs")

        playout = Playout.objects.all().last()

        endpoint_url = reverse("schedule-detail", kwargs={"playout_id": playout.id})

        logging.info("======> Get Schedule API (GET {})".format(endpoint_url))

        response = self.client.get(endpoint_url)

        logging.info("=========> should make sure that response is of array type")
        self.assertIsInstance(response.json(), list)
