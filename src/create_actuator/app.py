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

        # 2. Create unique actuator_id
        actuator_id = str(uuid.uuid4())

        # 3. Create a new actuator map with body data
        actuator_data = create_actuator_map(event)

        # 4. Create the actuator in DynamoDB
        response = create_actuator(event, actuator_data, actuator_id, pk)

        return build_response(200, response)
    except Exception as e:
        logger.error(f"Error creating actuator for user {pk}: {str(e)}")
        return build_response(500, {"error": "Internal Server Error"})
    
def create_actuator_map(event: Dict[str, Any]) -> Dict[str, Any]:
    body_raw = event.get("body") or "{}"
    body = json.loads(body_raw)

    actuator_name = body.get("actuator_name") or "Unnamed Actuator"

    # Create a new actuator map with default values
    return {
        "is_active": False,
        "name": actuator_name
    }

def create_actuator(event: Dict[str, Any], actuator_data: Dict[str, Any],actuator_id: str, pk: str) -> Dict[str, Any]:
    body_raw = event.get("body") or "{}"
    body = json.loads(body_raw)

    house_id = body.get("house_id") or ""
    actuator_name = body.get("actuator_name") or "Unnamed Actuator"
    
    logger.info(f"Creating actuator with ID: {actuator_id}, name: {actuator_name}, user_id: {pk}")

    response = table.update_item(
        Key={
            'user_id': pk,
            'house_id': house_id
        },
        UpdateExpression="SET actuators.#dynamic_actuator_id = :actuator_id",
        ExpressionAttributeNames={
            "#dynamic_actuator_id": actuator_id
        },
        ExpressionAttributeValues={
            ":actuator_id": actuator_data
        },
        ReturnValues="UPDATED_NEW"
    )

    return response.get("Attributes", {})


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