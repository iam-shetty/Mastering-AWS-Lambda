import boto3, os

def lambda_handler(event, context):
    r53 = boto3.client("route53")
    r53.change_resource_record_sets(
        HostedZoneId=os.environ["HOSTED_ZONE_ID"],
        ChangeBatch={
            "Changes": [{
                "Action": "UPSERT",
                "ResourceRecordSet": {
                    "Name": os.environ["RECORD_NAME"],
                    "Type": "A",
                    "AliasTarget": {
                        "HostedZoneId": os.environ["DR_LB_ZONE_ID"],
                        "DNSName": os.environ["DR_LB_DNS"],
                        "EvaluateTargetHealth": False
                    }
                }
            }]
        }
    )