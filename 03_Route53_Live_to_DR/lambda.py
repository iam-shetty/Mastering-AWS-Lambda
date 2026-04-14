import boto3, os

route53 = boto3.client("route53")

def lambda_handler(event, context):
    print("Failover started")

    route53.change_resource_record_sets(
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

    return {"status": "DNS switched to DR"}