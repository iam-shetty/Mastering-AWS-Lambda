# Mastering Lambda

### Automated IAM Access Key Detection & Cleanup

This project demonstrates a **real-world AWS security automation** built using **AWS Lambda and event-driven services**.

The goal is simple but critical:
**detect exposed IAM access keys and automatically clean them up before they cause damage**.

This is not a lab-style demo.
This is how you would approach **preventive security automation in production environments**.

---

## Why This Project Matters

Exposed IAM access keys are one of the most common causes of AWS account compromise.
Manual monitoring does not scale, and delayed response often leads to serious incidents.

This solution:

* Reacts automatically
* Notifies the right people
* Removes the risk without human intervention

All driven by events.

---

## High-Level Flow

1. An IAM access key is created or detected
2. An event is generated and routed via EventBridge
3. Lambda evaluates the event
4. Notifications are sent
5. The exposed access key is automatically deleted

---
## Implementation Breakdown

### Phase 1: Notification & Test Setup

* Created an SNS topic for security notifications
* Subscribed email endpoints to receive alerts
* Created a dummy IAM user to safely simulate access key exposure

This phase sets up visibility and a safe testing environment.

---

### Phase 2: Lambda & Event Configuration

* Created a dedicated IAM execution role for Lambda
* Attached only the required permissions
* Developed the Lambda function logic
* Configured EventBridge rules to trigger Lambda on relevant events
* Tested the end-to-end flow

This is the core automation layer where detection meets action.

---

### Phase 3: Automated Remediation

* Added triggers to invoke Lambda automatically
* Implemented logic to delete exposed IAM access keys
* Ensured cleanup happens without manual approval

Once triggered, the system acts immediately to remove risk.

---

## Design Principles Followed

* Event-driven architecture
* Least-privilege IAM
* Automation over manual intervention
* Safe testing using non-production users
* Clear separation of detection, notification, and remediation

---

## What This Proves