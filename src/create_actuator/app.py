import json
import logging
from typing import Any, Dict

import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

iot_client = boto3.client("iot-data")
client = boto3.client("dynamodb", region_name = "us-east-1")


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

    log("INFO", f"Request initiated by user {user_id}", {
        "requestId": request_id,
        "userId": user_id,
        "userEmail": user_id
    })

    try:
        body_raw = event.get("body") or "{}"
        body = json.loads(body_raw)
        state = body.get("state")
        house_id = body.get("house_id")
        actuator_id = body.get("actuator_id")
        actuator_name = body.get("actuator_name", "")
        actuator_value = body.get("actuator_value", False)

        response = client.transact_write_items(
            TransactItems=[
                {
                    "ConditionCheck": {
                        "TableName": "house-control-users-dev",
                        "Key": {
                            "PK": {"S": user_id},
                        },
                        "ConditionExpression": "contains(houses, :house_id)",
                        "ExpressionAttributeValues": {
                            ":house_id": {"S": house_id}
                        }
                    }
                },
                {
                    "Update": {
                        "TableName": "house-control-houses-dev",
                        "Key": {
                            "PK": {"S": house_id},
                        },
                        "UpdateExpression": "SET #actuators = if_not_exists(#actuators, :empty_map) #actuators.#act_id = :act_val",
                        "ExpressionAttributeNames": {
                            "#actuators": "actuators",
                            "#act_id": actuator_id
                        },
                        "ExpressionAttributeValues": {
                            ":empty_map": {"M": {}},
                            ":act_val": {
                                "M": {
                                    "name": {"S": actuator_name},
                                    "value": {"BOOL": actuator_value}
                                }
                            }
                        }
                    }
                }
            ]
        )

        return response
    
    except ClientError as e:
        logger.error(f"ClientError: {e.response['Error']['Message']}")
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"success": False, "error": e.response['Error']['Message']}),
        }

    