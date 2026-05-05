import boto3
import uuid

transcribe = boto3.client("transcribe")

def lambda_handler(event, context):
    job_name   = f"job-{uuid.uuid4()}"
    bucket     = event["bucket"]
    key        = event["key"]
    media_uri  = f"s3://{bucket}/{key}"

    # Derive format from file extension instead of hardcoding
    media_format = key.split(".")[-1].lower()

    transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={"MediaFileUri": media_uri},
        MediaFormat=media_format,   # dynamic — works for mp4, mov, avi
        IdentifyLanguage=True       # auto-detect — no hardcoded en-US
    )

    return {
        **event,
        "job_name": job_name
    }