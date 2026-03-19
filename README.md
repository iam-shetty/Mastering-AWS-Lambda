
# 🚀 Mastering Lambda


### Real-World AWS Lambda Projects | Production-Grade | Event-Driven Architecture

> **Mastering Lambda** is a hands-on repository focused on building **real-world, production-ready AWS Lambda projects**.
>
> This is **not theory**, **not toy examples**, and **not copy-paste demos**.
> Every project here solves a **real cloud problem** using **event-driven serverless design**, exactly how it’s done in real companies.

---

## 📌 What This Repository Is About

This repository contains **10 end-to-end AWS Lambda projects** (6 completed + 4 upcoming) that cover:

* Security automation
* Disaster recovery & failover
* Log processing & data masking
* Event-driven workflows
* AI-powered media pipelines
* Streaming & real-time processing

Each project is:

* ✅ Built step-by-step
* ✅ Event-driven (SNS, EventBridge, S3, CloudWatch, Kinesis, Step Functions)
* ✅ Focused on **real production use-cases**
* ✅ Designed with **least-privilege IAM** and best practices


## 🧠 Projects Included

### 🔐 1. IAM Access Key Auto-Rotation & Deletion

Automates detection and cleanup of exposed IAM access keys using SNS, EventBridge, and Lambda.

**Highlights**

* Detect leaked access keys
* Notify via email
* Automatically delete keys more than 90days

---

### 🛡️ 2. GuardDuty Automated Quarantine

Automatically isolates compromised EC2 instances when GuardDuty raises a finding.

**Highlights**

* GuardDuty → EventBridge → Lambda
* Applies quarantine security group
* Zero manual intervention

---

### 🌍 3. Multi-Region Disaster Recovery with Route53

Implements **automatic DNS failover** using Route53 health checks and Lambda.

**Highlights**

* Primary & DR regions
* Health-based failover
* SNS-driven Lambda execution

---

### 🧹 4. API Log Scrubber (PII Masking)

Cleans sensitive data from application logs before storing them securely in S3.

**Highlights**

* Masks emails, phone numbers, credit cards
* CloudWatch Logs → Lambda → S3
* Compliance-friendly logging

---

### ⚡ 5. Real-Time Fraud Detection with Kinesis

Processes streaming transactions in real time and stores suspicious activity in DynamoDB.

**Highlights**

* Kinesis stream trigger
* DynamoDB persistence
* Near real-time processing

---

### 🎬 6. AI-Powered Media Processing Pipeline

A complete **serverless media factory** using multiple AWS AI services.

**Highlights**

* S3 → Step Functions → Lambda
* Video analysis, transcription, metadata storage
* SNS notifications on completion


## 🚧 Upcoming Projects (In Progress)

* 🔄 Advanced Lambda Retry & DLQ Handling
* 🔐 Secrets & Config Management at Scale
* 📊 Cost-Optimized Serverless Analytics
* 🧠 GenAI + Lambda (Bedrock-based workflows)

> ⭐ Total Target: **10 Production-Grade Lambda Projects**

---

## 🛠️ Tech Stack Used

* AWS Lambda
* Amazon EventBridge
* Amazon SNS
* Amazon S3
* Amazon DynamoDB
* Amazon Kinesis
* AWS Step Functions
* Amazon GuardDuty
* Amazon Route53
* AWS AI Services (Rekognition, Transcribe, Bedrock)

---

## 🧩 Design Principles Followed

* Least-Privilege IAM
* Event-Driven Architecture
* Fault Tolerance
* Multi-Region Awareness
* Clean Separation of Responsibilities
* Production-ready structure

---

## 👨‍💻 Who This Is For

* Cloud & DevOps Engineers
* AWS Lambda Beginners → Advanced
* Serverless Architects
* Anyone tired of **“hello-world Lambda demos”**

If you’re serious about **mastering AWS Lambda in real-world scenarios**, this repository is built exactly for that purpose.

> **Learn less theory. Build more real systems.**
