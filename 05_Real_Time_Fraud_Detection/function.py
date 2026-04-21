import json
import boto3
import base64
import os
import statistics

# DynamoDB setup
ddb = boto3.resource("dynamodb")
table = ddb.Table(os.environ["FRAUD_TABLE"])

"""
   FRAUD_TABLE= environment variable that points to the DynamoDB table name where transactions are stored.
    """
def lambda_handler(event, context):
    """
    Processes Kinesis records, detects fraud signals,
    safely skips non-JSON / corrupt records.
    """

    for record in event.get("Records", []):
        try:
            # 1. Decode base64 payload from Kinesis
            raw_bytes = base64.b64decode(record["kinesis"]["data"])

            # 2. Decode bytes → string → JSON
            payload = raw_bytes.decode("utf-8")
            txn = json.loads(payload)

        except Exception as e:
            # Critical production safety
            print("SKIPPED_INVALID_RECORD", str(e))
            continue

        # 3. Fraud scoring
        score, reasons = evaluate(txn)
        decision = decide(score)

        # 4. Persist transaction
        store(txn)

        # 5. Log decision (audit evidence)
        print(json.dumps({
            "transaction_id": txn.get("transaction_id"),
            "user_id": txn.get("user_id"),
            "decision": decision,
            "score": score,
            "reasons": reasons
        }))


def evaluate(txn):
    score = 0
    reasons = []

    history = get_history(txn["user_id"])

    # High velocity transactions
    if len(history) >= 5:
        score += 30
        reasons.append("HIGH_VELOCITY")

    # Country mismatch
    if history and history[0].get("country") != txn.get("country"):
        score += 25
        reasons.append("GEO_MISMATCH")

    # Amount spike
    amounts = [h.get("amount", 0) for h in history]
    if amounts and txn.get("amount", 0) > statistics.mean(amounts) * 5:
        score += 20
        reasons.append("AMOUNT_SPIKE")

    # New device
    if history and history[0].get("device_id") != txn.get("device_id"):
        score += 15
        reasons.append("NEW_DEVICE")

    return score, reasons


def decide(score):
    if score >= 70:
        return "BLOCK"
    if score >= 40:
        return "REVIEW"
    return "ALLOW"


def get_history(user_id):
    """
    Fetch last 10 transactions for a user
    """
    resp = table.query(
        KeyConditionExpression="pk = :pk",
        ExpressionAttributeValues={
            ":pk": f"USER#{user_id}"
        },
        Limit=10,
        ScanIndexForward=False
    )
    return resp.get("Items", [])


def store(txn):
    """
    Store transaction in DynamoDB
    """
    table.put_item(
        Item={
            "pk": f"USER#{txn['user_id']}",
            "sk": f"TXN#{txn['timestamp']}",
            **txn
        }
    )
    """
    pk and sk are partion keys and sort key of Dynamo Db.
    """