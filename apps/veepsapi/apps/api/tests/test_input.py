import logging

from django.urls import reverse
from rest_framework import status

from . import VeepsTestCase
from .factories import PlayoutFactory, ChannelFactory, InputFactory
from ..models import Input, Playout

logger = logging.getLogger(__name__)


class InputTests(VeepsTestCase):
    def setUp(self):
        super().setUp()

        self.playout_data = PlayoutFactory()
        channel = ChannelFactory()
        channel.save()
        self.playout_data.channel = channel
        self.playout_data.save()

        input = InputFactory()
        input.playout = self.playout_data
        input.save()

    def test_input(self):
        logging.info("===> Testing Input APIs")

        # Create a playout if not exist already because it's needed for all input apis
        playout = Playout.objects.all().last()

        endpoint_url = reverse("input-list")

        logging.info("======> Create Input API (POST {})".format(endpoint_url))

        input_count_before_create = Input.objects.count()
        input_data = {
            "playout_id": playout.id,
            "name": "test_input_01",
            "protocol": "srt-listener",
            "port": 2000,
            "encryption": False,
            "cidr": "0.0.0.0/0",
        }
        create_response = self.client.post(endpoint_url, input_data, format="json")
        added_input = Input.objects.filter(name=input_data["name"]).first()

        logging.info("=========> should return status code 201")
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

        logging.info("=========> should store new input instance into input table")
        self.assertEqual(Input.objects.count(), input_count_before_create + 1)

        logging.info("=========> should make sure that new input instance has valid playout foreign key")
        self.assertNotEqual(added_input.playout, None)
        self.assertNotEqual(added_input.playout, "")
        self.assertNotEqual(added_input.playout.id, None)
        self.assertNotEqual(added_input.playout.id, "")

        logging.info("=========> should make sure that each fields of new input inserted in input table are correct")
        self.assertNotIn(added_input.id, [None, ""])
        self.assertEqual(added_input.name, input_data.get("name"))

        endpoint_url = reverse("input-list")

        logging.info("======> List Inputs API (GET {})".format(endpoint_url))
        list_response = self.client.get(endpoint_url)

        logging.info("=========> should return status code 200")
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)

        logging.info("=========> should make sure that response is of array type")
        self.assertIsInstance(list_response.json(), dict)

        logging.info("=========> should make sure that response results list length is correct")
        self.assertEqual(len(list_response.json().get("results")), 2)

        logging.info("=========> should make sure that response item has all required fields, and are correct")
        last_item = list_response.json().get("results")[-1]
        self.assertNotEqual(None, last_item)

        self.assertNotIn(last_item["id"], [None, ""])
        self.assertNotIn(last_item["playout_id"], [None, ""])
        self.assertNotIn(last_item["name"], [None, ""])
        self.assertNotIn(last_item["protocol"], [None, ""])

        endpoint_url = reverse("input-detail", kwargs={"playout_id": self.playout_data.id})

        input_update_data = {
            "input_id": last_item["id"],
            "state": "on",
        }

        logging.info("======> Update Input of Playout API (PUT {})".format(endpoint_url))
        update_response = self.client.patch(endpoint_url, data=input_update_data, format="json")

        logging.info("=========> should return status code 200")
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)

        update_data = update_response.json()

        logging.info("=========> should make sure that each fields of response are valid")
        self.assertEqual(update_data["state"], input_update_data.get("state"))

        self.assertNotEqual(None, added_input)

        logging.info("======> Delete Input of Playout API (DELETE {})".format(endpoint_url))

        delete_response = self.client.delete(endpoint_url, data={"input_id": last_item["id"]}, format="json")

        logging.info("=========> should return status code 204")
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

        logging.info("=========> should make sure that the instance gets deleted in input table")
        self.assertEqual(Input.objects.filter(pk=added_input.id).count(), 0)
