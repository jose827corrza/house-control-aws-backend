import json
import logging
from typing import Any, Dict

import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

iot_client = boto3.client("iot-data")


def log(level: str, message: str, extra: Dict[str, Any] = None) -> None:
    payload = {"level": level, "message": message}
    if extra:
        payload.update(extra)
    print(json.dumps(payload))


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    request_id = getattr(context, "aws_request_id", None)

    # 1. Extract JWT claims from requestContext
    authorizer = event.get("requestContext", {}).get("authorizer", {})
    claims = authorizer.get("jwt", {}).get("claims", {})

    # 2. Retrieve user identity fields
    user_id = claims.get("sub", "anonymous")
    user_email = claims.get("email", "unknown")
    username = claims.get("cognito:username", user_id)

    log("INFO", f"Request initiated by user {username}", {
        "requestId": request_id,
        "userId": user_id,
        "userEmail": user_email
    })

    try:
        body_raw = event.get("body") or "{}"
        body = json.loads(body_raw)
        state = body.get("state")

        if not isinstance(state, bool):
            log("WARN", "Invalid payload received", {"requestId": request_id, "user": user_id})
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"message": "Invalid payload: 'state' must be a boolean."}),
            }

        # Optionally publish user ID alongside the state to your IoT topic
        payload_data = {
            "state": state,
            "triggeredBy": user_id
        }

        iot_client.publish(
            topic=f"{user_id}/control",
            qos=1,
            payload=json.dumps(payload_data),
        )

        log("INFO", "Successfully published to IoT topic", {
            "requestId": request_id,
            "topic": "control",
            "state": state,
            "userId": user_id
        })

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "success": True,
                "message": f"Published {state} to {user_id}/control",
                "user": user_id
            }),
        }

    except json.JSONDecodeError as e:
        log("ERROR", "Invalid JSON format in body", {"requestId": request_id, "error": str(e)})
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"success": False, "error": "Malformed JSON payload."}),
        }
    except (BotoCoreError, ClientError) as e:
        log("ERROR", "Failed to publish to IoT", {"requestId": request_id, "error": str(e)})
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"success": False, "error": str(e)}),
        }