# Real-Time Fraud Detection System — AWS Kinesis + Lambda + DynamoDB

> A production-grade, serverless fraud detection pipeline for payment gateway transactions. Processes over 1,000 transactions per second using a risk-scoring engine built on velocity, geolocation, device fingerprinting, and amount spike analysis — fully automated, zero manual intervention required.

---

## 1. Project Overview

### The Problem

Banks process **over one million transactions per day**. Manual fraud detection at this scale is impossible. Two critical failure modes exist:

```
Block too aggressively  →  Genuine customers blocked  →  Customer dissatisfaction
Block too loosely       →  Fraudulent transactions pass  →  Financial loss
```

Neither extreme is acceptable. A **risk-based scoring system** is the industry answer — flag suspicious transactions for review rather than immediately block them.

### The Solution

A real-time serverless pipeline that:

- Ingests every transaction as a live stream event via **Kinesis**
- Scores each transaction in milliseconds via **Lambda**
- Stores flagged transactions for analyst review in **DynamoDB**
- Triggers automated customer verification (calls/SMS) for high-risk events

### Example Scenario

```
Normal behavior:
  User in India | Android | ₹500 | 10:00 AM IST | Known location

Suspicious event (same user, 4 hours later):
  Location  : Denmark        ← 25 points (geolocation anomaly)
  Device    : iPhone         ← 20 points (new device)
  Amount    : ₹90,000        ← 30 points (velocity spike)
  Time      : 2:00 AM IST    ← unusual hour
  ─────────────────────────────
  Total Score : 75 / 100     ← HIGH RISK → flagged for review
```

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Payment Gateway                              │
│                                                                     │
│   Transaction Events (1000+ per second)                             │
│        │                                                            │
│        ▼                                                            │
│   ┌─────────────────────┐                                          │
│   │   AWS Kinesis       │  ← Live streaming data ingestion         │
│   │   Data Stream       │    On-demand capacity                    │
│   └──────────┬──────────┘    Retains data for 24 hours             │
│              │                                                      │
│              │  triggers per shard batch                           │
│              ▼                                                      │
│   ┌─────────────────────┐                                          │
│   │   AWS Lambda        │  ← Fraud scoring engine                  │
│   │   fraud-aggregator  │    Python 3.12                           │
│   │                     │    60s timeout                           │
│   │   Scoring Logic:    │                                          │
│   │   • Velocity        │                                          │
│   │   • Geolocation     │                                          │
│   │   • Device type     │                                          │
│   │   • Amount spike    │                                          │
│   └──────────┬──────────┘                                          │
│              │                                                      │
│         ┌────┴────┐                                                │
│         ▼         ▼                                                │
│   ┌──────────┐  ┌─────────────────┐                               │
│   │ ALLOWED  │  │   DynamoDB      │  ← Flagged transactions        │
│   │ (low     │  │   fault-        │    stored for analyst review   │
│   │  score)  │  │   transaction   │                               │
│   └──────────┘  └────────┬────────┘                               │
│                           │                                        │
│                           ▼                                        │
│                  Security Team Review                              │
│                  + Automated Customer Call/SMS                     │
└─────────────────────────────────────────────────────────────────────┘

Monitoring: CloudWatch Logs + Metrics on every Lambda execution
```

---

## 3. Fraud Scoring Engine

Each transaction is evaluated against four risk dimensions. Scores accumulate and determine the risk level.

### Scoring Criteria

| Factor | Points | Trigger Condition |
|---|---|---|
| **Velocity** | 30 | Sudden spike in transaction amount vs historical average |
| **Geolocation** | 25 | Transaction from an unusual or new region/country |
| **Device Type** | 20 | New or different device from historical pattern |
| **Amount Spike** | 20 | Abnormal increase in single transaction amount |
| **Maximum Score** | **95** | All four factors triggered simultaneously |

### Risk Thresholds

```
Score  0 – 30   →  LOW RISK    →  Allow transaction
Score 31 – 60   →  MEDIUM RISK →  Flag for review, notify analyst
Score 61 – 95   →  HIGH RISK   →  Flag immediately, trigger customer verification call/SMS
```

### Why Not Binary Block/Allow?

```
Binary approach problems:
  Block all high-amount transactions  →  Blocks genuine large purchases
  Allow all transactions              →  Fraud passes through

Score-based approach benefits:
  ✅ Nuanced — considers context, not just amount
  ✅ Customer-friendly — genuine transactions rarely hit all four factors
  ✅ Auditable — every decision has a numeric justification
  ✅ Tunable — thresholds adjusted without code change
```

---

## 4. AWS Services Used

| Service | Role | Why This Service |
|---|---|---|
| **Kinesis Data Streams** | Real-time transaction ingestion | Handles 1,000+ events/second, built for streaming, retains data for replay |
| **Lambda** | Fraud scoring engine | Serverless, scales automatically per shard, no server management |
| **DynamoDB** | Flagged transaction storage | Single-digit millisecond reads, scales to any volume, TTL support |
| **CloudWatch** | Monitoring and logging | Captures all Lambda output, alerts on errors, dashboards |
| **IAM** | Access control | Least-privilege roles for Lambda → Kinesis → DynamoDB |

### Why Kinesis Over SQS?

```
SQS                              Kinesis
────────────────────────         ────────────────────────
Message queue                    Streaming platform
At-least-once delivery           Ordered within shard
No replay                        Replay up to 7 days
Good for tasks                   Good for event streams
Limited throughput               1MB/sec per shard (unlimited shards)

For payment transactions → Kinesis wins:
  ✅ Order matters (detect velocity across sequence of transactions)
  ✅ Replay needed (reprocess after Lambda bug fix)
  ✅ High throughput (1000+ tx/sec)
  ✅ Multiple consumers (fraud team + analytics team read same stream)
```

---

### Least-Privilege Lambda Policy (Production)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:ap-south-1:ACCOUNT_ID:table/fault-transaction"
    },
    {
      "Effect": "Allow",
      "Action": [
        "kinesis:GetRecords",
        "kinesis:GetShardIterator",
        "kinesis:DescribeStream",
        "kinesis:ListStreams",
        "kinesis:ListShards"
      ],
      "Resource": "arn:aws:kinesis:ap-south-1:ACCOUNT_ID:stream/fraud-stream"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

> I used `FullAccess` policies for speed. In production, always scope to specific table ARN and stream ARN as shown above.

---

## 14. Interview Q&A

**Q: Why Kinesis over SQS for this use case?**

Kinesis preserves event order within a shard — critical for velocity detection across a sequence of transactions from the same customer. SQS does not guarantee order. Kinesis also supports replay (reprocess last 7 days of events after a Lambda bug fix) and multiple consumers reading the same stream simultaneously.

**Q: What happens if Lambda fails mid-batch?**

Kinesis retries the entire batch until it succeeds or the record expires (24 hours default retention). This means a Lambda bug could cause the same transactions to be scored multiple times. The DynamoDB `put_item` is idempotent for the same `transaction_id` — duplicate writes overwrite with the same data, so no double-flagging occurs.

**Q: How does this scale to 1 million transactions per day?**

1 million per day = ~11.5 per second average, with peaks potentially 10x higher (~115/sec). Kinesis handles this with additional shards (each shard = 1MB/sec ingest). Lambda scales one concurrent invocation per shard automatically. DynamoDB on-demand scales to any write volume. No manual scaling required.

**Q: Why DynamoDB over RDS for storing flagged transactions?**

Fraud data access pattern is: "get all transactions for customer X" — a key-value lookup, not a complex SQL join. DynamoDB handles this in single-digit milliseconds at any scale. RDS would require connection pooling, schema migrations, and capacity planning. DynamoDB requires none of these.

**Q: How would you add a new scoring factor?**

Add a new function in `scoring.py`, assign it a point value, and add it to the `score_transaction` aggregation. Update the scoring documentation. No infrastructure changes required — Lambda deploys in seconds. Threshold tuning is a config change, not a code change.
