import boto3
import time

rekognition = boto3.client("rekognition")

def lambda_handler(event, context):
    bucket = event["detail"]["bucket"]["name"]
    key    = event["detail"]["object"]["key"]

    response = rekognition.start_label_detection(
        Video={
            "S3Object": {
                "Bucket": bucket,
                "Name":   key
            }
        },
        MinConfidence=70
    )
    job_id = response["JobId"]

    # Poll until job finishes
    while True:
        result = rekognition.get_label_detection(JobId=job_id)
        status = result["JobStatus"]

        if status == "SUCCEEDED":
            break
        elif status == "FAILED":
            raise Exception(f"Rekognition job failed: {job_id}")

        time.sleep(5)

    # Extract and deduplicate labels
    raw_labels = result.get("Labels", [])

    labels = [
        {
            "name":       item["Label"]["Name"],
            "confidence": round(item["Label"]["Confidence"], 2)
        }
        for item in raw_labels
    ]

    unique_labels = list(set(item["name"] for item in labels))

    return {
        "bucket":             bucket,
        "key":                key,
        "rekognition_job_id": job_id,
        "labels":             labels,
        "unique_labels":      unique_labels
    }