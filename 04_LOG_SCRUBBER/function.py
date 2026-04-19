import base64
import json
import gzip
import re
import boto3
import os
import uuid
from datetime import datetime

s3 = boto3.client("s3")

# ----------------------------
# PII REGEX DEFINITIONS
# ----------------------------
PII_PATTERNS = {
    "EMAIL": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
    "PHONE": r"\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}",
    "CREDIT_CARD": r"\b(?:\d[ -]*?){13,16}\b"
}

def scrub_pii(message: str) -> str:
    """Replace PII patterns with REDACTED tags"""
    for label, pattern in PII_PATTERNS.items():
        message = re.sub(pattern, f"[{label}_REDACTED]", message)
    return message


def lambda_handler(event, context):

    # ----------------------------
    # 1. Decode & decompress CW logs
    # ----------------------------
    compressed_payload = base64.b64decode(event["awslogs"]["data"])
    uncompressed_payload = gzip.decompress(compressed_payload)
    log_data = json.loads(uncompressed_payload)

    scrubbed_logs = []

    # ----------------------------
    # 2. Scrub each log event
    # ----------------------------
    for log_event in log_data.get("logEvents", []):
        original_message = log_event.get("message", "")
        scrubbed_message = scrub_pii(original_message)
        scrubbed_logs.append(scrubbed_message)

    if not scrubbed_logs:
        return {"status": "no_logs"}

    # ----------------------------
    # 3. SAFE S3 KEY (NO PII)
    # ----------------------------
    timestamp_prefix = datetime.utcnow().strftime("%Y/%m/%d/%H")
    unique_id = str(uuid.uuid4())

    s3_key = f"scrubbed/{timestamp_prefix}/{unique_id}.log"

    # ----------------------------
    # 4. Upload to S3
    # ----------------------------
    s3.put_object(
        Bucket=os.environ["CLEAN_LOG_BUCKET"],
        Key=s3_key,
        Body="\n".join(scrubbed_logs),
        ContentType="text/plain"
    )

    return {
        "status": "success",
        "records_processed": len(scrubbed_logs),
        "s3_key": s3_key
    }