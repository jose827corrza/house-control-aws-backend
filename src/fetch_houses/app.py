import json
import logging
import os
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

    # 1. Extract JWT claims from requestContext
    pk = get_user_id(event)

    try:
        logger.info(f"Request ID: {request_id} - Fetching actuators for user: {pk}")  
        response = table.query(
            KeyConditionExpression=Key('user_id').eq(pk)
        )

        raw_items = response.get("Items", [])
        logger.info(f"Request ID: {request_id} - Retrieved {len(raw_items)} items for user: {pk}")
        actuators_list =process_actuators(raw_items)

        return build_response(200, actuators_list)
    except Exception as e:
        logger.error(f"Error fetching actuators for user {pk}: {str(e)}")
        return build_response(500, {"error": "Internal Server Error"})


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

def process_actuators(raw_items: list) -> list:
    actuators_list = []

    for item in raw_items:
        logger.info(f"Processing item: {item}")

        actuators_map = item.get('actuators', {})
        
        # sk = item.get('house_id', '')

        actuators_list.append({
            "house_name": item.get('house_name', ''),
            "house_id": item.get('house_id', ''),
            "actuators": actuators_map,
        })
    return actuators_list

def build_response(status_code: int, body: Any) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "body": json.dumps(body),
        "headers": {
            "Content-Type": "application/json"
        }
    }