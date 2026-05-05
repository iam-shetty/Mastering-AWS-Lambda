import boto3
import time

rekognition = boto3.client("rekognition")

def lambda_handler(event, context):
    bucket = event["detail"]["bucket"]["name"]
    key = event["detail"]["object"]["key"]

    response = rekognition.start_label_detection(
        Video={
            "S3Object": {
                "Bucket": bucket,
                "Name": key
            }
        }
    )

    return {
        "bucket": bucket,
        "key": key,
        "rekognition_job_id": response["JobId"]
    }