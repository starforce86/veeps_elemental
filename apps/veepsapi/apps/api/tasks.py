import calendar
import hashlib
import hmac
import json
import time
import traceback

import requests

from apps.api import models
from apps.api import enums


def call_webhook(event_id):
    event = models.CallbackEvent.objects.get(id=event_id)
    callback_endpoint = event.subscriber.endpoint
    data = {"type": event.event_type, "object": json.loads(event.event_object)}
    try:
        session = requests.Session()
        request = requests.Request("POST", callback_endpoint, json=data)
        prepped = session.prepare_request(request)

        sig_timestamp = calendar.timegm(time.gmtime())
        sig_body = prepped.body
        payload = f"{sig_timestamp}.{sig_body}"
        signature = hmac.new(
            bytearray(event.subscriber.signing_secret.encode("utf-8")), payload.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        headers = {enums.WEBHOOK_SIGNATURE_HEADER_NAME: f"t={sig_timestamp},v1={signature}"}
        request = requests.Request("POST", callback_endpoint, json=data, headers=headers)
        prepped = session.prepare_request(request)

        response = session.send(prepped, verify=False, timeout=enums.INVOKE_CALLBACK_TIMEOUT)

        if 200 <= int(response.status_code) < 300:
            event.delivered_status = True
        event.save()
        models.CallbackLog.objects.create(
            playout_id=event.playout.id,
            callback_endpoint=callback_endpoint,
            headers=response.request.headers,
            body=response.request.body,
            response=response.json(),
            status_code=response.status_code,
            execution_time=response.elapsed.total_seconds(),
            sig_timestamp=sig_timestamp,
            sig_body=sig_body,
        )
    except Exception:
        models.CallbackLog.objects.create(
            playout_id=event.playout.id,
            callback_endpoint=callback_endpoint,
            headers=prepped.headers,
            body=prepped.body,
            sig_timestamp=sig_timestamp,
            sig_body=sig_body,
            exception=traceback.format_exc(),
        )

    event.retried_count += 1
    event.save()
