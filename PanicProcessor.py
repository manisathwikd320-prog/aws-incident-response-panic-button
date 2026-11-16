import json
import os
from datetime import datetime, timezone
import boto3

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")
sns = boto3.client("sns")
table = dynamodb.Table("PanicButtonState")

DEVICE_ID = "panic-button-01"

def lambda_handler(event, context):
    print("Event Received:", json.dumps(event))
    
    # Get device ID and current time
    device_id = event.get("deviceId", DEVICE_ID)
    now = datetime.now(timezone.utc).isoformat()

    try:
        # 1) Update DynamoDB to reflect the incident
        table.update_item(
            Key={"deviceId": device_id},
            UpdateExpression="SET #s = :s, lastUpdated = :t",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={
                ":s": "INCIDENT_ACTIVE",
                ":t": now,
            },
        )
        print("DynamoDB updated successfully.")

        # 2) Simulate the remediation playbook (log to CloudWatch)
        print(f"[PLAYBOOK] {now} — Public access blocked (Simulated)")

        # 3) Send SNS Email Alert
        topic_arn = os.environ.get("TOPIC_ARN")
        if topic_arn:
            sns.publish(
                TopicArn=topic_arn,
                Subject="CRITICAL: Panic Button Triggered",
                Message=(
                    f"🚨 INCIDENT DETECTED 🚨\n\n"
                    f"Device ID: {device_id}\n"
                    f"Timestamp: {now}\n\n"
                    f"The incident response playbook has been executed:\n"
                    f"  • DynamoDB state set to INCIDENT_ACTIVE\n"
                    f"  • Public access blocked (simulated)\n"
                    f"  • This alert dispatched"
                ),
            )
            print("SNS Alert sent successfully.")
        else:
            print("WARNING: TOPIC_ARN environment variable not set.")

        return {
            "statusCode": 200, 
            "body": json.dumps({"message": "Incident processed successfully"})
        }
        
    except Exception as e:
        print(f"Error processing incident: {str(e)}")
        raise e