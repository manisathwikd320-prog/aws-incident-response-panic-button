"""
AWS Lambda Function: PanicGetter
Runtime: Python 3.12
Region: ap-southeast-2
Author: Incident Response System Team

Description:
Reads the latest status of a panic button device from DynamoDB
and serves it via Lambda Function URL with CORS headers.
"""

import json
import decimal
import time
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

# ==========================================
# Configuration
# ==========================================
REGION_NAME = "ap-southeast-2"
TABLE_NAME = "PanicButtonState"
DEFAULT_DEVICE_ID = "panic-button-01"

# Initialize DynamoDB resource outside handler for connection reuse
dynamodb = boto3.resource("dynamodb", region_name=REGION_NAME)
table = dynamodb.Table(TABLE_NAME)

# Standard CORS headers
CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type,Authorization"
}


# ==========================================
# JSON Encoder for DynamoDB Decimal types
# ==========================================
class DecimalEncoder(json.JSONEncoder):
    """Encodes DynamoDB Decimal types into int or float for JSON compatibility."""
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            if obj % 1 == 0:
                return int(obj)
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def lambda_handler(event, context):
    """
    AWS Lambda entry point for Function URL or API Gateway.
    """
    print(f"[EVENT] Received event: {json.dumps(event)}")

    # Extract HTTP method (supports HTTP API / Function URL payload v2.0 and REST API v1.0)
    http_method = ""
    if "requestContext" in event and "http" in event["requestContext"]:
        http_method = event["requestContext"]["http"].get("method", "").upper()
    elif "httpMethod" in event:
        http_method = event.get("httpMethod", "").upper()

    # 1. Handle CORS Preflight (OPTIONS)
    if http_method == "OPTIONS":
        print("[INFO] Handling CORS preflight OPTIONS request.")
        return {
            "statusCode": 204,
            "headers": CORS_HEADERS,
            "body": ""
        }

    # 2. Extract Device ID from Query Parameters (Fallback to default)
    device_id = DEFAULT_DEVICE_ID
    query_params = event.get("queryStringParameters") or {}
    if query_params and "deviceId" in query_params:
        device_id = query_params["deviceId"]

    # 3. Retrieve state from DynamoDB
    try:
        response = table.get_item(Key={"deviceId": device_id})
        item = response.get("Item")

        if item:
            print(f"[SUCCESS] Record retrieved for {device_id}: {item}")
            # Ensure standard fields exist if backend stored varied schemas
            status_payload = dict(item)
            if "status" not in status_payload:
                # If backend stored 'state' or 'action' instead
                status_payload["status"] = status_payload.get("state", "UNKNOWN")
        else:
            print(f"[WARNING] No record found in table '{TABLE_NAME}' for deviceId: '{device_id}'. Returning default.")
            current_unix = int(time.time())
            status_payload = {
                "deviceId": device_id,
                "status": "UNKNOWN",
                "action": "NONE",
                "timestamp": current_unix,
                "lastUpdated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "message": "No state record found for device in DynamoDB"
            }

        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps(status_payload, cls=DecimalEncoder)
        }

    except ClientError as e:
        error_msg = e.response.get("Error", {}).get("Message", str(e))
        print(f"[ERROR] DynamoDB ClientError: {error_msg}")
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({
                "error": "InternalServerError",
                "message": error_msg,
                "deviceId": device_id,
                "status": "ERROR"
            })
        }
    except Exception as e:
        print(f"[ERROR] Unexpected exception: {str(e)}")
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({
                "error": "InternalServerError",
                "message": str(e),
                "deviceId": device_id,
                "status": "ERROR"
            })
        }
