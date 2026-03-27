### 🛡️ 2. AWS GuardDuty Automation: Automated Quarantine of Compromised EC2 Instances

**This project provides a production-grade automation solution to handle security compromises in AWS EC2 instances. It addresses the critical need for hard evidence (snapshots and documentation) required by security and Payment Card Industry (PCI) audit teams during annual reviews.Instead of relying on manual intervention, this system uses AWS GuardDuty to detect "fishy" behavior—such as unauthorized logins or the installation of cryptocurrency mining software—and triggers an immediate, automated response**

## The following AWS services are central to this project:

1. **AWS GuardDuty**: This is the core detection service. Unlike standard monitoring tools, it specifically analyzes the behavior of resources to identify "misbehavior," such as unauthorized logins or the installation of cryptocurrency mining software
When it detects suspicious activity, it generates "findings" with specific severity levels.

2. **Amazon EventBridge**: Acting as the connective tissue, EventBridge is configured with an event pattern to monitor GuardDuty
When GuardDuty generates a finding—specifically those with high severities (7, 8, or 9)—EventBridge triggers the remediation process by notifying the target Lambda function

3. **AWS Lambda**: This service handles the automated remediation. Once triggered by EventBridge, the Lambda function executes a Python script that performs several critical actions: it removes the instance's existing security groups, assigns a quarantine security group, and initiates an EBS snapshot of the instance for later investigation

4. **Amazon EC2 (Elastic Compute Cloud)**: These are the virtual servers being protected
. In this project, an instance is launched within a custom VPC to demonstrate how the automation reacts when a compromise is detected

5. **Amazon VPC (Virtual Private Cloud) & Security Groups**: The project involves creating a dedicated VPC network environment
Security Groups are used as virtual firewalls; specifically, a "quarantine" security group is created with no inbound or outbound rules to completely isolate a compromised instance from the internet and the rest of the network

6. **AWS IAM (Identity and Access Management)**: IAM is used to manage the necessary permissions for the automation to work
This includes creating a Lambda execution role that allows the function to describe instances, modify attributes, and create snapshots
It also involves an EC2 role (using the Amazon SSM Managed Instance Core policy) so the instance can be managed even while isolated

7. **Amazon EBS (Elastic Block Store) Snapshots**: These are used to capture a point-in-time record of the compromised instance's disk
These snapshots are critical for forensic investigations, allowing security teams to perform root cause analysis by creating an Amazon Machine Image (AMI) to safely inspect the intruder's tools and actions in an isolated environment

8.**AWS Systems Manager (SSM)**: While mentioned primarily in the context of IAM policies, SSM permissions are attached to the EC2 instances to ensure they remain reachable for legitimate administrative purposes during the quarantine process

## 1. Project Overview

### The Problem

In large AWS environments (37+ accounts, 100+ EC2 instances), manually detecting and responding to a compromised EC2 instance is too slow. By the time a human notices unusual behavior — crypto-mining software, unauthorized access, lateral movement — the attacker has had hours to operate.

Security and PCI-DSS audit teams ask:
- What precautions are you taking to protect 100+ EC2 instances?
- Can you show evidence, not just tell us?
- What happens the moment an instance is compromised?

**Oral answers are not accepted. Evidence is required.**

### The Solution

An automated incident response pipeline:

```
Threat Detected → Isolated in < 60 seconds → Evidence Preserved → Team Notified
```

| Metric | Value |
|---|---|
| Mean Time to Contain (MTTC) | < 60 seconds |
| Human intervention required | Zero (automated) |
| Accounts supported | Multi-account via STS |
| Compliance output | PCI-DSS audit evidence |
| Forensic preservation | EBS snapshot on every incident |

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        AWS Environment                          │
│                                                                 │
│   EC2 Instance                                                  │
│   (Compromised)                                                 │
│       │                                                         │
│       │ behavior detected                                       │
│       ▼                                                         │
│   ┌──────────────┐     finding      ┌─────────────────┐        │
│   │  GuardDuty   │ ──────────────► │   EventBridge   │        │
│   │  (Watchman)  │                 │  severity 7,8,9  │        │
│   └──────────────┘                 └────────┬────────┘        │
│                                             │ trigger          │
│                                             ▼                  │
│                                    ┌─────────────────┐        │
│        ┌── SSM Parameter Store ──► │ Lambda Function │        │
│        │   (quarantine SG ID)      │  (Responder)    │        │
│        │                           └────────┬────────┘        │
│        │                    ┌───────────────┼──────────────┐   │
│        │                    ▼               ▼              ▼   │
│        │           Quarantine SG      EBS Snapshot    IAM Deny │
│        │           (zero rules)       (forensics)    (all APIs)│
│        │                                                        │
│        └──────────────────────────────────────────────────────┐│
│                                                               ▼│
│                                                    SNS → Security Team
│                                                               ││
│                                                    DynamoDB ◄─┘│
│                                                    (orig SG ID) │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Why Each Service Exists

### The Chain of Gaps — Why Every Service Is Necessary

Each service in this pipeline exists because the previous one has a gap it cannot fill alone.

| Service | Its Job | Why Not Something Else? |
|---|---|---|
| **GuardDuty** | Detects threat behavior | CloudWatch only monitors metrics (CPU/RAM), not behavior. GuardDuty understands crypto-mining patterns, lateral movement, credential theft |
| **EventBridge** | Routes findings to Lambda | An email alert requires a human to read, decide, and act — takes minutes. EventBridge reacts in milliseconds, automatically |
| **Lambda** | Executes response logic | A script on a server might itself be compromised. Lambda runs in isolated AWS infrastructure with its own minimal IAM role |
| **Quarantine SG** | Cuts network access | Terminating the instance destroys forensic evidence. Quarantine SG freezes the attacker mid-action while keeping the instance alive |
| **EBS Snapshot** | Preserves disk state | Without a snapshot, the security team has no point-in-time evidence to mount and investigate |
| **IAM Deny policy** | Blocks AWS API calls | Network isolation alone isn't enough — a running process could still call AWS APIs via instance metadata. Deny-all IAM stops this |
| **SNS** | Notifies humans | Alert fires AFTER automated containment. Team receives a clear report to investigate calmly, not scramble during a live attack |
| **DynamoDB** | Stores original SG ID | Lambda must save the original SG ID before swapping it — otherwise rollback is impossible |
| **SSM Parameter Store** | Stores quarantine SG ID | Never hardcode infrastructure IDs. SSM allows changing the quarantine SG ID without redeploying Lambda |

---

## 4. AWS Services — Detailed Workflow

### Phase 1 — Detection (GuardDuty)

GuardDuty continuously analyzes three data sources:
- **CloudTrail logs** — API call history
- **VPC Flow Logs** — network traffic metadata
- **DNS logs** — domain lookup patterns

When it detects malicious behavior, it raises a **Finding** — a structured JSON event


Finding severity scale:
- **1–3** → Low (informational)
- **4–6** → Medium (investigate)
- **7–9** → High/Critical → **triggers our pipeline**

---

### Phase 2 — Routing (EventBridge)

EventBridge listens for GuardDuty findings and filters by severity:

Only HIGH severity findings trigger Lambda. This prevents alert fatigue and false isolations from low-severity noise.

**Target:** Lambda function in the same account (or cross-account via STS for multi-account setups).

---

### Phase 3 — Response (Lambda)

Lambda receives the EventBridge event, extracts the instance ID, and executes three simultaneous actions:


#### Action 1 — Swap Security Group (Quarantine)

#### Action 2 — Create EBS Snapshot

#### Action 3 — Attach Deny-All IAM Policy

### Phase 4 — Isolation (Quarantine Security Group)

The quarantine SG has **zero inbound rules and zero outbound rules**.

AWS security groups are deny-by-default. With no rules added:
- Every inbound packet is dropped — attacker loses shell access
- Every outbound packet is dropped — malware C2 callbacks fail
- The EC2 instance keeps running — forensic state is preserved

**Before quarantine:**
```
Internet ──► Port 443 (HTTPS) ──► EC2
Internet ──► Port 22  (SSH)   ──► EC2
EC2      ──► 0.0.0.0/0        ──► Internet
```

**After quarantine:**
```
Internet ──► [DROPPED]  ──► EC2
EC2      ──► [DROPPED]  ──► Internet
```

The attacker is frozen mid-action. The instance is alive. Evidence is intact.

### Phase 5 — Forensics (EBS Snapshot + IAM Deny)

**EBS Snapshot:**
- Point-in-time copy of the compromised disk
- Security team mounts it on a clean forensic EC2 instance
- Investigates malware artifacts, bash history, cron jobs, installed packages
- Original compromised instance remains untouched

**IAM Deny-All:**
- Applied as an inline policy on the instance IAM role
- Prevents any running process from calling AWS APIs
- Even if the attacker has code running that tries `s3:GetObject` or `ec2:DescribeInstances` — denied
- Stops lateral movement to other AWS resources

---

### Phase 6 — Notification (SNS)

After all automated actions complete, Lambda publishes to SNS:

```
Subject: EC2 Compromise — Automated Response Complete

Instance ID   : i-0abc1234def567890
Finding Type  : CryptoCurrency:EC2/BitcoinTool.B
Severity      : 8 (High)
Time          : 2025-03-20T10:00:00Z

Actions Taken:
  ✅ Security group swapped to quarantine (sg-quarantine-xxxx)
  ✅ EBS snapshot created (snap-forensic-xxxx)
  ✅ IAM deny-all policy attached
  ✅ Original SG ID saved to DynamoDB

Next Steps:
  1. Review finding in GuardDuty console
  2. Mount snapshot on forensic instance
  3. Run rollback Lambda when investigation complete
```

SNS fans out to: Email, Slack, PagerDuty — whoever is on call.

---

### Phase 7 — Rollback (DynamoDB + Restore Lambda)

When investigation is complete, a separate rollback Lambda:

```python
# Reads original SG from DynamoDB
original_sgs = dynamodb.get_item(Key={'instance_id': instance_id})

# Reattaches original SG
ec2.modify_instance_attribute(
    InstanceId=instance_id,
    Groups=original_sgs
)

# Removes deny-all IAM policy
iam.delete_role_policy(
    RoleName=instance_role,
    PolicyName='SecurityDenyAll'
)

# Updates DynamoDB status
dynamodb.update_item(status='RESTORED')
```



## 8. Interview Q&A — DevSecOps Panel
## 8. Interview Q&A — DevSecOps Panel

---

### Q1: What happens after quarantine? Who owns the forensic process?

**Answer:**

After quarantine, ownership follows a clear chain:

**Lambda automatically (< 500ms):**
- Creates EBS snapshot tagged `forensic-investigation`
- Publishes SNS alert to security-incidents channel
- Logs all actions to CloudWatch

**L1 Security Analyst (within 15 minutes):**
- Validates the GuardDuty finding severity
- Pulls CloudTrail logs, VPC Flow Logs, SSM Session history
- Confirms it is a true positive, not a false positive

**L2 / Incident Response Team:**
- Mounts EBS snapshot on a clean forensic EC2 instance
- Runs malware analysis tools
- Documents root cause — how did the attacker enter, what did they do

**Decision gate:**
- Low severity → sanitize and restore instance
- High severity → terminate, recreate from golden AMI
- Critical → escalate to CISO, preserve for legal proceedings

---

### Q2: How did you handle false positives? What if GuardDuty flags a legit admin?

**Answer:**

We handle this at two levels — prevention and detection.

**Prevention (before isolation fires):**
- SSM Parameter Store holds a whitelist of exempt instance IDs and IAM roles
- Lambda checks whitelist before changing any security group
- Break-glass admin roles are always on the whitelist
- GuardDuty suppression rules configured for known scanner IPs and trusted IP ranges

**Detection (after a false positive fires):**
- CloudTrail captures every Lambda API call with full audit trail
- SNS alert fires to both the security team AND the instance owner simultaneously
- Owner has a 10-minute window to raise false positive via runbook before full isolation completes

**Tuning over time:**
- GuardDuty trusted IP list maintained and reviewed monthly
- Weekly false positive review in security standup
- Suppression rules added for known internal tools (vulnerability scanners, pen test IPs)

---

### Q3: How did you manage this across multiple accounts?

**Answer:**

We use AWS Organizations with a dedicated Security Tooling account as the hub — hub and spoke model.

**Architecture:**
- Security account = GuardDuty delegated administrator
- Security account = central EventBridge bus
- Lambda runs in Security account only

**Member accounts each have:**
```
IAM Role: SecurityResponseRole
Trust policy: allows Security account to assume it
Permissions: ec2:ModifyInstanceAttribute, ec2:CreateSnapshot, iam:PutRolePolicy
```

**Cross-account flow:**
1. GuardDuty finding fires in member account
2. Aggregated to Security account via AWS Organizations integration
3. EventBridge triggers Lambda in Security account
4. Lambda calls `STS:AssumeRole` on member account's `SecurityResponseRole`
5. Uses temporary credentials to isolate EC2 in that member account

**Key security principle:** `SecurityResponseRole` has only the exact permissions needed — nothing more.

---

### Q4: What is your rollback mechanism if Lambda isolates the wrong instance?

**Answer:**

Rollback was specifically designed into the architecture from day one.

**Before isolation, Lambda does this first:**
```python
# Step 1 — Read current SG IDs
original_sgs = describe_instance_security_groups(instance_id)

# Step 2 — Save to DynamoDB
dynamodb.put_item({
    'instance_id': instance_id,
    'original_sgs': original_sgs,
    'isolated_at': datetime.utcnow().isoformat(),
    'finding_id': guardduty_finding_id,
    'status': 'QUARANTINED'
})

# Step 3 — THEN swap to quarantine SG
ec2.modify_instance_attribute(Groups=[QUARANTINE_SG_ID])
```

**Rollback Lambda (separate function, triggered manually):**
- Triggered only via approved change ticket — not automatic
- Reads original SGs from DynamoDB
- Reattaches them to the instance
- Removes quarantine SG and deny-all IAM policy
- Updates DynamoDB status to `RESTORED`
- Publishes audit log to CloudTrail and CloudWatch

**Why DynamoDB?**
- Survives Lambda crashes or timeouts
- Account-level — accessible from security account cross-account
- Full audit trail of every isolation and restoration event
- Queryable — security team can see all quarantined instances at a glance

---

### Q5: How did you store the quarantine security group ID securely?

**Answer:**

We use SSM Parameter Store — not Secrets Manager. The distinction matters.

**Why SSM Parameter Store over Secrets Manager:**
- A security group ID is not a secret — it is a configuration value
- Secrets Manager costs $0.40 per secret per month per account
- Parameter Store Standard tier is free
- Secrets Manager is purpose-built for credentials, API keys, passwords — not infrastructure config

**Implementation:**
```
Parameter path:
  /security/guardduty/dev/quarantine-sg-id
  /security/guardduty/prod/quarantine-sg-id
```

**Lambda fetches at runtime:**
```python
response = ssm.get_parameter(
    Name='/security/guardduty/prod/quarantine-sg-id',
    WithDecryption=False
)
QUARANTINE_SG = response['Parameter']['Value']
```

**Benefits:**
- Change the quarantine SG ID without redeploying Lambda
- Full Parameter Store audit trail — who changed it, when
- Environment-specific paths — dev and prod never share the same value
- IAM policy on Lambda role scoped to `/security/guardduty/*` only


