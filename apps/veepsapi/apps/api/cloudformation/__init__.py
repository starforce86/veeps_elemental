import json
import logging

import botocore.exceptions
from ..utils import get_boto_client

from config import settings

logger = logging.getLogger(__name__)


class CloudFormationStackGeneric:
    def __init__(self):
        self.stack_name = None
        self.template = None
        self.stack_id = None
        self.cloudformation_client = get_boto_client("cloudformation")
        self.stack_id = None
        self.old_stack_name = None

    @staticmethod
    def get_boto_client(resource_name):
        return get_boto_client(resource_name)

    def create_template(self):
        raise NotImplementedError()

    def get_outputs(self):
        stack = self.cloudformation_client.describe_stacks(StackName=self.stack_name)

        return stack.get("Stacks")[0].get("Outputs", [])

    def get_output_value(self, key):
        outputs = self.get_outputs()
        val = None

        for output in outputs:
            if output["OutputKey"] == key:
                val = output["OutputValue"]

        return val

    @property
    def json(self):
        return self.template.to_json()

    @property
    def minified_json(self):
        json_data = json.loads(self.json)
        minified_data = json.dumps(json_data, separators=(",", ":"))
        return minified_data

    def create(self, region=None):
        if self.stack_name is None:
            raise NotImplementedError("stack_name must be set in order to create a cloudformation stack")

        if region is None:
            region = settings.AWS_DEFAULT_REGION

        notification_arn = f"arn:aws:sns:{region}:{settings.AWS_ACCOUNT_NUMBER}:{settings.AWS_SNS_TOPIC}"
        try:
            response = self.cloudformation_client.create_stack(
                StackName=self.stack_name,
                TemplateBody=self.minified_json,
                NotificationARNs=[notification_arn],
            )
        except botocore.exceptions.ClientError as err:
            logger.error(f"Couldn't create cloudformation template \n {err}")
            # try creating without the notification ARN
            response = self.cloudformation_client.create_stack(
                StackName=self.stack_name,
                TemplateBody=self.minified_json,
            )

        logger.info(response)
        return response

    def update_change_set(self, region=None):
        if region is None:
            region = settings.AWS_DEFAULT_REGION

        # Create the change set
        notification_arn = f"arn:aws:sns:{region}:{settings.AWS_ACCOUNT_NUMBER}:{settings.AWS_SNS_TOPIC}"

        change_set_name = f"{self.stack_name}change"

        # Create the change set
        self.cloudformation_client.create_change_set(
            StackName=self.stack_name,
            ChangeSetName=change_set_name,
            TemplateBody=self.minified_json,
            ChangeSetType="UPDATE",
            NotificationARNs=[notification_arn]
            # UsePreviousTemplate=True,
        )

        # Wait for the changeset to update, so that the change set can be applied
        # time.sleep(15)
        status = ""
        while status != "CREATE_COMPLETE":
            stuff = self.cloudformation_client.describe_change_set(
                ChangeSetName=change_set_name,
                StackName=self.stack_name,
            )

            status = stuff["Status"]

        self.cloudformation_client.execute_change_set(
            StackName=self.stack_name,
            ChangeSetName=change_set_name,
        )

    def update(self):
        """
        :return: Success: Boolean, (Message: String)
        """
        try:
            if self._stack_exists():
                logger.info(f"Updating {self.old_stack_name}")
                stack_result = self.cloudformation_client.update_stack(
                    StackName=self.old_stack_name,
                    TemplateBody=self.minified_json,
                )
                logger.info(stack_result)
                return True, ""
            return False, "No Stack with such name and ARN exists"
        except botocore.exceptions.ClientError as ex:
            error_message = ex.response["Error"]["Message"]
            logger.error(error_message)

            if error_message == "No updates are to be performed.":
                return True, ""

            return False, error_message

    def delete(self):
        response = self.cloudformation_client.delete_stack(
            StackName=self.stack_name,
        )
        logger.info(response)
        return response

    def _stack_exists(self):
        stacks = self.cloudformation_client.list_stacks()["StackSummaries"]
        logger.info(f"Checking if stack with info {self.stack_id} can be modified")
        for stack in stacks:
            if stack.get("StackStatus", None) == "DELETE_COMPLETE":
                continue
            if self.stack_id == stack.get("StackId", None):
                self.old_stack_name = stack.get("StackName", None)
                return True
        return False

    def get_status(self):
        try:
            response = self.cloudformation_client.describe_stacks(
                StackName=self.stack_name,
            )
        except botocore.exceptions.ClientError as err:
            logger.info(f"Stack already deleted {err}")
            return "DELETE_COMPLETE"

        status = response.get("Stacks")[0].get("StackStatus", None)
        if status is None:
            logger.error(f"Stack {self.stack_name} has no status")
        return status


def get_response_for_stack_manipulation(cloud_formation_response):
    """
    :param cloud_formation_response:
    :return: ARN of the stack if the response was parsed correctly
    """
    metadata = cloud_formation_response.get("ResponseMetadata", {})
    status_code = metadata.get("HTTPStatusCode", None)
    error = cloud_formation_response.get("error", None)
    stack_id = cloud_formation_response.get("StackId", None)

    logger.info({"detail": error, "stack_id": stack_id, "status_code": status_code})

    if status_code == 200:
        return stack_id
    return None
