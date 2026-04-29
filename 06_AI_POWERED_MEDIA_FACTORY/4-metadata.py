import boto3
import os

ddb = boto3.resource("dynamodb")
table = ddb.Table(os.environ["METADATA_TABLE"])

def lambda_handler(event, context):
    table.put_item(
        Item={
            "VideoName": event["key"],      # Partition key
            "Bucket": event["bucket"],
            "Labels": event.get("labels", []),
            "Summary": event["summary"],
            "Status": event["status"]       # ✅ THIS WAS MISSING
        }
    )

    return {
        "status": "SUCCESS",
        "Status": event["status"],
        "video": event["key"]
    }