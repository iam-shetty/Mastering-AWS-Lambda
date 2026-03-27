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



