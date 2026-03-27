### 🛡️ 2. AWS GuardDuty Automation: Automated Quarantine of Compromised EC2 Instances

***This project provides a production-grade automation solution to handle security compromises in AWS EC2 instances. It addresses the critical need for hard evidence (snapshots and documentation) required by security and Payment Card Industry (PCI) audit teams during annual reviews.Instead of relying on manual intervention, this system uses AWS GuardDuty to detect "fishy" behavior—such as unauthorized logins or the installation of cryptocurrency mining software—and triggers an immediate, automated response

## The following AWS services are central to this project:

1. **AWS GuardDuty**: This is the core detection service. Unlike standard monitoring tools, it specifically analyzes the behavior of resources to identify "misbehavior," such as unauthorized logins or the installation of cryptocurrency mining software
.When it detects suspicious activity, it generates "findings" with specific severity levels.


