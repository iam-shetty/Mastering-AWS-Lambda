import boto3
import os

ec2 = boto3.client('ec2')

ddb = boto3.resource('dynamodb')
sns = boto3.client('sns')

TABLE = os.environ.get("TABLE_NAME", "ZombieResourceTracker")
TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")

def lambda_handler(event, context):
    table = ddb.Table(TABLE)

    volumes = ec2.describe_volumes(
        Filters=[{"Name": "status", "Values": ["available"]}]
    )["Volumes"]

    for v in volumes:
        vid = v["VolumeId"]

        table.put_item(
            Item={
                "vid": vid,
                "Type": "EBS",
                "Status": "ZOMBIE"
            }
        )

        sns.publish(
            TopicArn=TOPIC_ARN,
            Subject="Zombie resource detected",
            Message=f"Unattached EBS volume found: {vid}"
        )

    return {"zombies": len(volumes)}