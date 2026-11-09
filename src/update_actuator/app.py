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

    try:

        # 1. Extract JWT claims from requestContext
        pk = get_user_id(event)

        # 2. Fetch and update the Map value in DynamoDB
        response = update_dynamic_actuators_map(event, pk, request_id)

        return build_response(200, response)
    except Exception as e:
        logger.error(f"Error updating actuator for user {pk}: {str(e)}")
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

def update_dynamic_actuators_map(event: Dict[str, Any], pk: str, request_id: Any) -> Dict[str, Any]:
        body_raw = event.get("body") or "{}"
        body = json.loads(body_raw)

        house_id = body.get("house_id") or ""
        actuator_id = body.get("actuator_id") or ""
        actuator_state = body.get("actuator_state") or False
    
        logger.info(f"Request Body: act_id:{type(actuator_id)}.. value: {actuator_id} - act_state:{type(actuator_state)}.. value: {actuator_state} - house_id:{type(house_id)}.. value: {house_id} - user_id:{type(pk)}.. value: {pk}")  
        response = table.update_item(
            Key={
                'user_id': pk,
                'house_id': house_id
            },
            UpdateExpression=(
                "SET actuators.#dynamic_actuator_id.is_active = :value"
                 ),
            ExpressionAttributeNames={
                '#dynamic_actuator_id': actuator_id
            },
            ExpressionAttributeValues={
                ':value': actuator_state
            },
            ReturnValues="UPDATED_NEW"
        )

        return response.get('Attributes', {})

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