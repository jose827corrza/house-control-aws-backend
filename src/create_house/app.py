import json
import logging
import os
import uuid
from typing import Any, Dict

import boto3
from boto3.dynamodb.conditions import Key


logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamo = boto3.resource("dynamodb")
TABLE_NAME = os.environ.get("HOUSES_TABLE_NAME", "house-control-table")
table = dynamo.Table(TABLE_NAME)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    request_id = getattr(context, "aws_request_id", None)

    try:

        # 1. Extract JWT claims from requestContext
        pk = get_user_id(event)

        # 2. Create unique house_id
        house_id = str(uuid.uuid4())

        response = create_house(event, house_id, pk)

        return build_response(200, response)
    except Exception as e:
        logger.error(f"Error creating house for user {pk}: {str(e)}")
        return build_response(500, {"error": "Internal Server Error"})

def create_house(event: Dict[str, Any], house_id: str, pk: str) -> Dict[str, Any]:
    body_raw = event.get("body") or "{}"
    body = json.loads(body_raw)

    house_name = body.get("house_name") or "Unnamed House"
    actuators_map = body.get("actuators_map") or {}

    logger.info(f"Creating house with ID: {house_id}, name: {house_name}, user_id: {pk}")

    item = {
            'user_id': pk,
            'house_id': house_id,
            'house_name': house_name,
            'actuators': actuators_map
    }
    response = table.put_item(Item=item)

    return item

def get_user_id(event: Dict[str, Any]) -> str:
    authorizer = event.get("requestContext", {}).get("authorizer", {})
    claims = authorizer.get("jwt", {}).get("claims", {})

    # 2. Retrieve user identity fields
    user_id = claims.get("sub", "anonymous")
    user_email = claims.get("email", "unknown")
    username = claims.get("cognito:username", user_id)

    logger.info(f"Extracted user_id: {user_id}, email: {user_email}, username: {username}")
    # Placeholder for actual logic to retrieve user_id
    return username

def build_response(status_code: int, body: Any) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "body": json.dumps(body),
        "headers": {
            "Content-Type": "application/json"
        }
    }