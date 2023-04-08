import logging

from django.urls import reverse
from rest_framework import status

from . import VeepsTestCase
from ..models import Playout, Channel, Input, StateOptions

logger = logging.getLogger(__name__)


class PlayoutTests(VeepsTestCase):
    def setUp(self):
        super().setUp()

        self.playout_data = {
            "resolution": "HD",
        }

    # Create one playout in aws to test,
    # this one playout will be used for overall tests instead of creating multiple playouts in aws
    def test_create_playout(self):
        logging.info("===> Testing Playout APIs")

        endpoint_url = reverse("playout-list")

        logging.info("======> Create Playout API (POST {})".format(endpoint_url))

        create_response = self.client.post(endpoint_url, self.playout_data, format="json")

        self.assertEquals(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Playout.objects.count(), 1)

        added_playout = Playout.objects.all().last()

        logging.info("=========> should make sure that new playout instance has valid channel foreign key")

        self.assertIsNotNone(added_playout.channel)
        self.assertNotIn(added_playout.channel.id, [None, ""])

        logging.info(
            "=========> should make sure that each fields of new playout instance in playout table are correct"
        )

        self.assertNotIn(added_playout.id, [None, ""])
        self.assertEqual(added_playout.resolution, self.playout_data["resolution"])
        self.assertNotEqual(added_playout.status, StateOptions.ON)
        self.assertNotIn(added_playout.created_on, [None, ""])

        logging.info("=========> should store new channel instance into channel table")

        self.assertEqual(Channel.objects.count(), 1)

        logging.info(
            "=========> should make sure that each fields of new channel instance in channel table are correct"
        )

        added_channel = Channel.objects.all().last()

        self.assertNotIn(added_channel.name, [None, ""])
        self.assertNotIn(added_channel.description, [None, ""])
        self.assertNotIn(added_channel.created_on, [None, ""])
        self.assertNotIn(added_channel.updated_on, [None, ""])

        self.assertEqual(added_channel.state, StateOptions.OFF)

        self.assertIn(added_channel.schedule, [None, ""])

        logging.info("=========> should store new input into input table")

        self.assertEqual(Input.objects.count(), 1)

        logging.info("=========> should make sure that each fields of new input inserted in input table are correct")

        added_input = Input.objects.filter(playout_id=added_playout.id).first()
        self.assertIsNotNone(added_input)

        self.assertNotIn(added_input.created_on, [None, ""])
        self.assertNotIn(added_input.updated_on, [None, ""])
        self.assertNotIn(added_input.protocol, [None, ""])
        self.assertNotIn(added_input.port, [None, ""])
        self.assertNotIn(added_input.encryption, [None, ""])
        self.assertNotIn(added_input.whitelist_cidr, [None, ""])
        self.assertNotIn(added_input.name, [None, ""])
        self.assertNotIn(added_input.playout.id, [None, ""])
        self.assertNotIn(added_input.initial_input, [None, ""])
        self.assertEqual(added_input.state, StateOptions.OFF)

        logging.info("=========> should make sure that response json has all required fields, and are as expected")

        self.assertNotIn(create_response.json()["id"], [None, ""])
        self.assertEqual(create_response.json()["resolution"], self.playout_data["resolution"])
        self.assertNotIn(create_response.json()["created_on"], [None, ""])

        endpoint_url = reverse("playout-list")

        logging.info("======> List Playouts API (GET {})".format(endpoint_url))

        list_response = self.client.get(endpoint_url)

        logging.info("=========> should return status code 200")
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)

        response_json = list_response.json()

        logging.info("=========> should make sure that response has results field of array type")
        self.assertIsInstance(response_json["results"], list)

        logging.info("=========> should make sure that response results list length is correct")
        self.assertEqual(len(response_json["results"]), 1)

        logging.info("=========> should make sure that response has count field of integer type")
        self.assertEqual(response_json["count"], 1)

        logging.info(
            "=========> should make sure that response results field item has all required fields, and are correct"
        )
        # we asserted previously that the list should only have one result, so we can just pop it out of the list
        added_input = response_json.get("results")[0]
        self.assertNotIn(added_input["id"], [None, ""])
        self.assertEqual(added_input["resolution"], self.playout_data["resolution"])
        self.assertEqual(added_input["status"], "")
        self.assertNotIn(added_input["created_on"], [None, ""])

        self.assertNotEqual(None, added_playout)
        endpoint_url = reverse("playout-detail", kwargs={"playout_id": added_playout.id})

        logging.info("======> Get Playout API (GET {})".format(endpoint_url))

        get_response = self.client.get(endpoint_url)

        logging.info("=========> should return status code 200")
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)

        logging.info("=========> should make sure that response has all required fields, and are correct")
        self.assertNotIn(get_response.data.get("id"), [None, ""])
        self.assertNotIn(get_response.data.get("created_on"), [None, ""])

        self.assertEqual(get_response.data.get("resolution"), self.playout_data["resolution"])

        self.assertIn(get_response.data.get("status"), "")

        self.assertNotEqual(None, added_playout)
        delete_endpoint = reverse("playout-detail", kwargs={"playout_id": added_playout.id})

        logging.info("======> Delete Playout API (DELETE {})".format(delete_endpoint))
        delete_response = self.client.delete(delete_endpoint, format="json")

        logging.info("=========> should return status code 204")
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

        logging.info("=========> should make sure that the instance gets deleted in playout table")
        self.assertEqual(Playout.objects.all().count(), 0)
