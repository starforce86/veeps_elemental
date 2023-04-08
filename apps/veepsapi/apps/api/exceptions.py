import json
import sys
import traceback

from django.http import Http404
from rest_framework import exceptions
from rest_framework.exceptions import APIException, ValidationError  # pylint: disable=unused-import
from rest_framework.views import exception_handler


def custom_exception_handler_simple(exc, context):
    if isinstance(exc, exceptions.ValidationError):
        pass
    elif isinstance(exc, Http404):
        pass
    else:
        detail = str(exc)
        exc_type, value, tb = sys.exc_info()
        if is_json(detail) and json.loads(detail).get("message"):
            detail = json.loads(detail).get("message")
        exc = ValidationError(detail={"detail": detail, "traceback": traceback.format_exception(exc_type, value, tb)})

    return exception_handler(exc, context)


def is_json(myjson):
    try:
        json.loads(myjson)
    except ValueError:
        return False
    return True
