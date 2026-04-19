# PCI-Compliant Log Scrubber — Automated Sensitive Data Redaction Pipeline
> A production-grade AWS serverless pipeline that automatically detects and
> redacts sensitive customer data (card numbers, phone numbers, PII) from
> application logs in real time — triggered by CloudWatch Log Groups via
> subscription filters, processed by Lambda, and stored as clean audit artifacts
> in S3. Built to satisfy PCI-DSS and internal security audit requirements.
---

1. Problem Statement
The Business Reality
In payment and e-commerce applications, every customer action generates logs:
```
Customer logs in     → username, email written to log
Customer pays        → card number, phone number written to log
Customer updates     → PII details written to log
```
These logs land in CloudWatch Log Groups and get shipped to S3 buckets.
The Compliance Problem
```
Security Team Audit Question:
"Your application says 'data is encrypted' at checkout.
 But we can see raw card numbers in your S3 logs.
 Explain this."

This is a PCI-DSS violation.
This is an internal escalation.
This can result in fines, audit failures, loss of payment processing licence.
```
What  I Built
An automated Lambda pipeline that:
Watches CloudWatch log groups via subscription filters
Triggers instantly when any log event arrives
Scrubs sensitive fields using regex patterns
Stores clean, redacted logs in S3
Never requires human intervention
```
Before scrubbing:
  {"user": "john", "card": "4111-1111-1111-1111", "phone": "9876543210"}

After scrubbing:
  {"user": "[REDACTED]", "card": "[REDACTED]", "phone": "[REDACTED]"}
```
---
2. Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Payment Application                      │
│                    (any live app)                           │
└──────────────────────────┬──────────────────────────────────┘
                           │ writes logs
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              CloudWatch Log Group                           │
│         /aws/lambda/demo-app                                │
│                                                             │
│   ┌─────────────────────────────┐                          │
│   │   Subscription Filter       │                          │
│   │   Pattern: (any log event)  │                          │
│   │   Target: Lambda function   │                          │
│   └──────────────┬──────────────┘                          │
└──────────────────┼──────────────────────────────────────────┘
                   │ invokes (real time)
                   ▼
┌─────────────────────────────────────────────────────────────┐
│              Lambda Function                                │
│              api-log-scrubber                               │
│                                                             │
│   1. Decode gzip compressed log data                        │
│   2. Parse JSON log events                                  │
│   3. Apply regex patterns — redact sensitive fields         │
│   4. Write clean log to S3                                  │
└──────────────────────────┬──────────────────────────────────┘
                           │ writes scrubbed file
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              S3 Bucket                                      │
│              scrubbing-logs-bucket                          │
│                                                             │
│   scrubbed/2026/01/20/log-<timestamp>.json                 │
│   → audit-ready, PCI-safe, redacted logs                   │
└─────────────────────────────────────────────────────────────┘
```
---
3. Why Each Service Was Chosen
Service	Role	Why Not Something Else?
CloudWatch Log Group	Receives all app logs	Standard AWS logging destination — every Lambda, ECS task, EC2 with agent writes here automatically
Subscription Filter	Triggers Lambda on every log event	Real time — fires within seconds of log arrival. S3 event notification is only for object uploads, not log streams
Lambda	Scrubs the log data	Serverless — scales to zero when no logs, scales to thousands when traffic spikes. No server to manage
Regex patterns	Finds sensitive data	Language-agnostic, fast, works on any log format regardless of which app generated it
S3	Stores scrubbed logs	Cheap, durable (99.999999999%), queryable with Athena, lifecycle policies for auto-deletion
IAM Role	Lambda permissions	Principle of least privilege — Lambda only gets what it needs
Resource Policy	CloudWatch → Lambda permission	CloudWatch is a different AWS service — it needs explicit permission to invoke Lambda cross-service
---
4. How It Works — Full Workflow
Step 1 — Application Writes a Log
Your payment app or Lambda function logs customer activity:
```python
# Somewhere in your application
logger.info(json.dumps({
    "user": "john",
    "email": "john@example.com",
    "card": "4111-1111-1111-1111",
    "phone": "9876543210",
    "action": "payment_initiated"
}))
```
This goes to CloudWatch Log Group automatically.
---
Step 2 — Subscription Filter Detects the Log
The subscription filter watches the log group. The moment a log event arrives:
```
Log Group receives event
         │
         ▼
Subscription Filter checks:
  Does this match the filter pattern?
  (empty pattern = match everything)
         │
         ▼
  YES → invoke Lambda immediately
        pass the log data as the event payload
```
---
Step 3 — CloudWatch Sends Compressed Data to Lambda
CloudWatch does NOT send raw JSON to Lambda. It sends:
```
Base64 encoded
└── gzip compressed
    └── JSON object containing:
        {
          "messageType": "DATA_MESSAGE",
          "owner": "123456789012",
          "logGroup": "/aws/lambda/demo-app",
          "logStream": "2026/01/20/[$LATEST]abc123",
          "logEvents": [
            {
              "id": "event-id",
              "timestamp": 1737388800000,
              "message": "{\"user\":\"john\",\"card\":\"4111-1111-1111-1111\"...}"
            }
          ]
        }

Lambda must: base64 decode → gzip decompress → JSON parse
```
---
Step 4 — Lambda Scrubs the Data
For each log event message, Lambda applies regex patterns:
```
Input:
  {"user": "john", "card": "4111-1111-1111-1111", "phone": "9876543210"}

Regex pass 1 — card pattern:
  \d{4}-\d{4}-\d{4}-\d{4}
  Finds: 4111-1111-1111-1111
  Replaces with: [REDACTED]

Regex pass 2 — phone pattern:
  \b\d{10}\b
  Finds: 9876543210
  Replaces with: [REDACTED]

Regex pass 3 — username pattern:
  "user"\s*:\s*"[^"]*"
  Finds: "user": "john"
  Replaces: "user": "[REDACTED]"

Output:
  {"user": "[REDACTED]", "card": "[REDACTED]", "phone": "[REDACTED]"}
```
---
Step 5 — Clean Log Written to S3
```python
s3.put_object(
    Bucket="scrubbing-logs-bucket",
    Key=f"scrubbed/{year}/{month}/{day}/log-{timestamp}.json",
    Body=scrubbed_log_content
)
```
Result in S3:
```
scrubbing-logs-bucket/
└── scrubbed/
    └── 2026/
        └── 01/
            └── 20/
                └── log-1737388800.json  ← clean, audit-safe file
```
---



    
```
---
10. DevOps Scenario Interview Q&A
---
Q1: What is log scrubbing and why is it needed in a payment application?
Answer:
Log scrubbing is the automated process of detecting and removing or masking sensitive data from application logs before they are stored or shipped to log aggregation systems.
In a payment application, every customer transaction generates logs. Without scrubbing, these logs can contain raw card numbers, phone numbers, email addresses, and usernames. If these logs land in S3 or CloudWatch in plaintext, they represent a direct PCI-DSS violation — because the application promises customers their data is encrypted, but the logs tell a different story.
The consequence is an internal escalation from the security team during an audit. They will ask for evidence that sensitive data is protected at rest. The scrubbing pipeline IS that evidence.
---
Q2: Why did you use CloudWatch Subscription Filters instead of EventBridge to trigger the Lambda?
Answer:
EventBridge is designed for AWS service events — GuardDuty findings, S3 object uploads, scheduled jobs. It does not natively stream CloudWatch log events in real time.
Subscription filters are purpose-built for this use case. They attach directly to a log group and stream every matching log event to a destination — Lambda, Kinesis, or another log group — within seconds of the log being written.
For log scrubbing, latency matters. If a card number sits in a log for 5 minutes before being redacted, that is 5 minutes of exposure. Subscription filters react in near-real time — typically under 5 seconds.
---
Q3: Why does CloudWatch send gzip-compressed base64-encoded data to Lambda instead of raw JSON?
Answer:
Two reasons — efficiency and transport safety.
Gzip compression: Application logs can be very large. A single log batch might be hundreds of kilobytes. Gzip typically achieves 70-80% compression on JSON text. This reduces Lambda payload size, speeds up invocation, and reduces data transfer costs.
Base64 encoding: Lambda event payloads must be valid JSON. Binary data like gzip output cannot be embedded directly in JSON — JSON does not support raw binary. Base64 converts binary to ASCII text that is safe to include in a JSON string.
So the pipeline is: gzip the log data → base64 encode it → embed in JSON → send to Lambda. Lambda reverses: base64 decode → gzip decompress → parse JSON.
---
Q4: What is the difference between a resource policy and an IAM role policy? Why do you need both here?
Answer:
An IAM role policy controls what an identity can DO — it is attached to the Lambda execution role and says "this Lambda can write to S3, read from SSM, create CloudWatch log groups."
A resource policy controls who can ACCESS a resource — it is attached to the Lambda function itself and says "CloudWatch Logs service is allowed to invoke this function."
You need both because AWS uses a two-sided permission model for cross-service invocations. The IAM role handles outbound permissions — what Lambda can reach. The resource policy handles inbound permissions — who can trigger Lambda.
Without the resource policy, CloudWatch Logs would get an access denied error when trying to invoke Lambda, even if the subscription filter is correctly configured.
---
Q5: Your regex pattern might miss a card number formatted differently. How would you handle this in production?
Answer:
Regex is a first-pass defence, not a complete solution. It works well for known formats but fails for unknown or obfuscated formats.
In production we layer multiple approaches. First, regex for known patterns — card numbers, phone numbers, emails. Second, AWS Macie — an ML-powered service that scans S3 objects for sensitive data it was trained to recognise across hundreds of formats. Third, structured log enforcement — instead of scrubbing freeform text, we require all application logs to use a defined JSON schema where sensitive fields are never logged in the first place — only masked representations like last four digits of a card.
The scrubbing Lambda is the safety net for when application code accidentally logs something it should not. The real fix is developer education and log schema enforcement at the application level.
---
Q6: What happens if Lambda fails mid-scrubbing? Does the sensitive log persist?
Answer:
Yes — and this is the most important gap in a basic implementation.
If Lambda crashes after CloudWatch sends the log but before S3 write completes, the original log event still exists in CloudWatch. CloudWatch does not delete log events — they persist for the retention period configured on the log group (default forever, should be set to 30-90 days for compliance).
The production fix is three-fold. First, set CloudWatch Log Group retention to the minimum required by compliance — typically 30 days — so raw logs auto-expire. Second, use a dead letter queue on the subscription filter so failed Lambda invocations are captured and can be reprocessed. Third, enable Lambda destinations — on failure, send the unprocessed payload to an SQS queue for retry with exponential backoff.
The scrubbing pipeline reduces exposure. It does not eliminate the window of exposure entirely. That window is closed by log retention policies and application-level masking before logging.
---
Q7: How would you scale this to 37 AWS accounts and multiple applications?
Answer:
The single-account setup becomes a multi-account pattern using AWS Organizations and centralized logging.
Each member account ships its CloudWatch logs to a central Log Archive account via cross-account CloudWatch log subscriptions. The scrubbing Lambda lives in the Log Archive account and processes all logs from all accounts in one place. IAM resource policies on the Lambda allow each member account's CloudWatch Logs service to invoke it.
For multiple applications, instead of one Lambda, we use one Lambda per sensitivity classification. Payment application logs go through the full PCI scrubber with card, phone, email, and name patterns. Internal tooling logs go through a lighter scrubber with just email patterns. The subscription filter pattern on each log group routes to the appropriate Lambda.
Infrastructure is managed with Terraform — one module per scrubber type, deployed across all accounts via CloudFormation StackSets.
---
Q8: How do you prove this is working to a PCI auditor?
Answer:
Evidence is everything in a PCI audit. We provide four artefacts.
First, the S3 bucket contents — auditors can sample scrubbed log files and confirm sensitive fields are redacted. The S3 files are the primary evidence.
Second, CloudWatch Lambda invocation metrics — show that the scrubber ran for every log event. Gaps in invocations mean uninspected logs, which is a finding.
Third, the subscription filter configuration — exported as Terraform state or AWS Config snapshot — proves the scrubber is attached to the correct log groups and cannot be bypassed.
Fourth, AWS Macie scan results on the S3 bucket — Macie actively checks for sensitive data in S3. A clean Macie report is the strongest possible evidence that the scrubbing is effective.
---
11. Production Readiness Checklist
```
Feature                         Basic Setup    Production Grade
──────────────────────────────  ───────────    ────────────────
Regex scrubbing                 ✅             ✅
Environment variables           ✅             ✅
CloudWatch trigger              ✅             ✅
Error handling                  ❌             ✅ try/except + DLQ
Dead letter queue               ❌             ✅ SQS DLQ for failures
Log retention policy            ❌             ✅ 30-90 days max
S3 server-side encryption       ❌             ✅ SSE-KMS
S3 bucket versioning            ❌             ✅ enabled
Macie scan on S3 output         ❌             ✅ weekly scan
Multi-account support           ❌             ✅ cross-account log sub
Terraform IaC                   ❌             ✅ all resources in code
CI/CD pipeline                  ❌             ✅ GitHub Actions
CloudWatch alarm on errors      ❌             ✅ SNS alert on failure
Lambda function versioning      ❌             ✅ published alias
S3 lifecycle policy             ❌             ✅ archive to Glacier 90d
```
---
12. Resume — STAR Format Bullet
```
STAR Format:
  S — Situation  (context and problem)
  T — Task       (your responsibility)
  A — Action     (what you built)
  R — Result     (measurable outcome)
```
Single STAR Bullet (for Resume / LinkedIn)
```
• Designed and deployed a serverless PCI-DSS log scrubbing pipeline on AWS
  to eliminate sensitive data exposure in payment application logs — identified
  as a critical compliance gap during security audit; built a Lambda function
  triggered in real time via CloudWatch subscription filters that applies regex
  scrubbing patterns to redact card numbers, phone numbers, and PII from log
  events before writing audit-safe artefacts to S3, reducing sensitive data
  exposure window from indefinite retention to under 5 seconds across all
  application log streams.
```
Breakdown of Why Each Part Is Strong
```
"PCI-DSS log scrubbing pipeline"
  → compliance keyword — recruiters and auditors recognise this immediately

"identified as a critical compliance gap during security audit"
  → shows you work in environments with real audits and real stakes

"real time via CloudWatch subscription filters"
  → shows you know the RIGHT tool — not just "used Lambda"

"regex scrubbing patterns to redact card numbers, phone numbers, and PII"
  → specific — shows you understand what sensitive data looks like technically

"audit-safe artefacts to S3"
  → shows you understand the output is evidence, not just storage

"reducing sensitive data exposure window to under 5 seconds"
  → quantified result — this is what separates strong bullets from weak ones
```
Shorter Version (if resume space is tight)
```
• Built a serverless AWS log scrubbing pipeline (Lambda + CloudWatch
  subscription filters + S3) that automatically redacts PCI-sensitive data
  — card numbers, phone numbers, PII — from payment application logs in real
  time, closing a compliance gap identified during PCI-DSS audit and reducing
  sensitive data exposure window to under 5 seconds.
```
---
13. Cleanup
```bash
# Delete Lambda function
aws lambda delete-function --function-name api-log-scrubber

# Delete CloudWatch Log Group
aws logs delete-log-group --log-group-name /aws/lambda/demo-app

# Delete subscription filter (if log group still exists)
aws logs delete-subscription-filter \
  --log-group-name /aws/lambda/demo-app \
  --filter-name log-scrapper

# Empty and delete S3 bucket
aws s3 rm s3://scrubbing-logs-bucket --recursive
aws s3api delete-bucket --bucket scrubbing-logs-bucket

# Delete IAM role (detach policies first)
aws iam detach-role-policy \
  --role-name lambda-basic-role-scrapper \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam detach-role-policy \
  --role-name lambda-basic-role-scrapper \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

aws iam delete-role --role-name lambda-basic-role-scrapper
```
---
Raise a PR to improve regex patterns or add new sensitive data types.
This is a living document — update as compliance requirements evolve.