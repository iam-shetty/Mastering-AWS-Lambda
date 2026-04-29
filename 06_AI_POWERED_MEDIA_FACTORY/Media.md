# Production-Grade AI Video Content Moderation Pipeline — AWS Serverless + Generative AI

> An event-driven, fully serverless content moderation pipeline that automatically analyzes uploaded videos for unsafe content and foul language using AWS Rekognition, Transcribe, and Bedrock (Amazon Titan) — zero human review required for standard content decisions.

[![AWS](https://img.shields.io/badge/AWS-Serverless-orange)](https://aws.amazon.com/serverless/)
[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)
[![Step Functions](https://img.shields.io/badge/AWS-Step%20Functions-purple)](https://aws.amazon.com/step-functions/)
[![Generative AI](https://img.shields.io/badge/GenAI-Amazon%20Bedrock-green)](https://aws.amazon.com/bedrock/)

---


---

## 1. Project Overview

### The Problem

Platforms like YouTube, Udemy, and any video streaming service receive thousands of video uploads every day. No human team can watch every video before it goes live. Manual moderation is:

```
Slow      →  Hours or days before a video is approved
Expensive →  Human reviewers at scale cost millions
Inconsistent → Different reviewers apply different standards
Unscalable   → Works at 100 videos/day, fails at 100,000/day
```

### The Solution

A fully automated AI pipeline that triggers the moment a video is uploaded:

```
Video uploaded to S3
       │
       ▼ (milliseconds)
Pipeline starts automatically
       │
       ├── Visual analysis    (Rekognition)  → detects explicit imagery
       ├── Audio analysis     (Transcribe)   → detects foul language
       └── AI summarization   (Bedrock)      → generates moderation verdict
                                                  │
                                    ┌─────────────┴─────────────┐
                                    ▼                           ▼
                               SAFE → deploy              UNSAFE → block
                               Status stored in DynamoDB
                               Team notified via SNS
```

### Real-World Context

This mirrors exactly how production content platforms operate. The system has been designed based on real production implementations — the same pattern used by streaming platforms to protect their communities at scale without manual overhead.

---

## 2. Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         Content Upload Flow                              │
│                                                                          │
│  Video Creator                                                           │
│      │                                                                   │
│      │  uploads MP4                                                      │
│      ▼                                                                   │
│  ┌──────────────────┐                                                   │
│  │   Amazon S3      │  raw-media-uploads bucket                         │
│  │  (Source)        │  EventBridge notification enabled                 │
│  └────────┬─────────┘                                                   │
│           │  ObjectCreated event fires                                   │
│           ▼                                                              │
│  ┌──────────────────┐                                                   │
│  │  EventBridge     │  Event pattern: source = S3                      │
│  │  (Router)        │  Target = Step Functions state machine            │
│  └────────┬─────────┘                                                   │
│           │  invokes                                                     │
│           ▼                                                              │
│  ┌──────────────────────────────────────────────────────────────┐       │
│  │              AWS Step Functions — State Machine               │       │
│  │                                                              │       │
│  │  Step 1          Step 2           Step 3         Step 4      │       │
│  │  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐ │       │
│  │  │ Video    │──►│ Video    │──►│ Video    │──►│ Video    │ │       │
│  │  │ Analyzer │   │Transcriber│  │Summarizer│   │ Metadata │ │       │
│  │  │          │   │          │   │          │   │  Saver   │ │       │
│  │  │Rekognition│  │Transcribe│   │ Bedrock  │   │ DynamoDB │ │       │
│  │  └──────────┘   └──────────┘   └──────────┘   └──────────┘ │       │
│  └──────────────────────────────────────────────────────────────┘       │
│                                                                          │
│  ┌──────────────────┐    ┌──────────────────┐                           │
│  │    DynamoDB      │    │      SNS         │                           │
│  │ media-metadata   │    │  Email Alerts    │                           │
│  │ (verdict store)  │    │  (team notify)   │                           │
│  └──────────────────┘    └──────────────────┘                           │
└──────────────────────────────────────────────────────────────────────────┘
```

### Why Step Functions Instead of a Single Lambda?

```
Single Lambda approach:
  One function does everything → timeout after 15 minutes
  If Transcribe takes 5 minutes → Lambda times out
  No visibility into which step failed
  Cannot retry individual steps

Step Functions approach:
  Each AI service gets its own Lambda → own timeout
  Visual pipeline dashboard → see exactly which step is running
  Retry individual failed steps without restarting the whole pipeline
  Wait states handle async AI operations (Transcribe takes minutes)
  Full execution history stored automatically
```

---

## 3. AWS Services Used

| Service | Role | Why This Service |
|---|---|---|
| **S3** | Video storage and pipeline trigger | Scales to petabytes, native EventBridge integration |
| **EventBridge** | Event routing | Decouples S3 from Step Functions — S3 doesn't need to know what processes it |
| **Step Functions** | Pipeline orchestration | Manages multi-step AI workflow, handles wait states, visual debugging |
| **Lambda (x4)** | Execution layer | Serverless, each function scoped to one AI service |
| **Rekognition** | Visual content analysis | Pre-trained AWS AI — detects explicit content, violence, unsafe scenes |
| **Transcribe** | Speech-to-text | Converts video audio to text for language analysis |
| **Bedrock (Amazon Titan)** | AI verdict generation | Summarizes Rekognition + Transcribe outputs into a final moderation decision |
| **DynamoDB** | Verdict storage | Single-digit millisecond writes, schema-flexible for varying AI outputs |
| **SNS** | Team notifications | Email/SMS alerts when processing starts and completes |

---

## 4. The Four Lambda Functions

### Why Four Functions Instead of One?

Each AI service has a different processing time and failure mode. Separating them into individual Lambda functions means:

```
Function 1 — Video Analyzer    ~10-30 seconds  (Rekognition is fast)
Function 2 — Video Transcriber  ~2-10 minutes   (Transcribe is async — needs wait state)
Function 3 — Video Summarizer  ~5-15 seconds   (Bedrock inference)
Function 4 — Metadata Saver     ~1-2 seconds    (DynamoDB write)

If Transcribe fails → only retry Function 2, not the whole pipeline
If Bedrock times out → only retry Function 3
Each function is independently testable and debuggable
```

### Function Summary

| Function | AI Service | Input | Output |
|---|---|---|---|
| `video-analyzer` | Rekognition | S3 bucket + key | Visual moderation labels + confidence scores |
| `video-transcriber` | Transcribe | S3 bucket + key | Full transcript text |
| `video-summarizer` | Bedrock (Titan) | Labels + transcript | Moderation verdict (SAFE/UNSAFE) + summary |
| `video-metadata-saver` | DynamoDB | Full analysis results | Stored verdict in DynamoDB |

---

## 5. AI Services — How Each One Works

### Rekognition — Visual Analysis

```
What it does:
  Analyzes video frames for visual content
  Returns moderation labels with confidence percentages

Example output:
  {
    "ModerationLabels": [
      {"Name": "Explicit Nudity",  "Confidence": 98.5},
      {"Name": "Graphic Violence", "Confidence": 45.2},
      {"Name": "Safe Content",     "Confidence": 99.1}
    ]
  }

What it catches:
  Explicit imagery
  Graphic violence
  Suggestive content
  Unsafe scenes

What it cannot do:
  Understand spoken words (that is Transcribe's job)
  Context-aware decisions (that is Bedrock's job)
```

### Transcribe — Audio Analysis

```
What it does:
  Separates audio track from video
  Converts speech to text (transcription)
  Supports 100+ languages

Why async?
  For a 10-minute video, Transcribe takes 2-5 minutes
  Lambda cannot simply wait — it would timeout
  Step Functions uses a WAIT state:
    Lambda starts the Transcribe job → returns job ID
    Step Functions waits 120 seconds
    Next Lambda polls for completion
    Retries until Transcribe finishes

Example output:
  "Today in today's session I'm going to show you 
   how AI is actually used in real companies..."
```

### Bedrock (Amazon Titan) — AI Verdict

```
What it does:
  Receives: Rekognition labels + Transcribe transcript
  Uses Amazon Titan text model for inference
  Produces: Human-readable moderation summary + SAFE/UNSAFE verdict

Why Bedrock and not a simple if/else?
  Context matters:
    "Violence" in a cooking video → knife scenes → safe
    "Violence" in a horror clip   → graphic scenes → unsafe
    Foul language in a documentary about censorship → acceptable
    Foul language targeted at a person → unacceptable
  
  Bedrock understands context. An if/else does not.

Model used: amazon.titan-text-express-v1
  (titan-text-lite-v1 reached end-of-life — use Express)

Example prompt to Bedrock:
  "You are a content moderator. Based on the following 
   visual analysis and transcript, determine if this 
   video is SAFE or UNSAFE for a general audience.
   
   Visual analysis: [Rekognition output]
   Transcript: [Transcribe output]
   
   Respond with: STATUS (SAFE/UNSAFE), REASON, SUMMARY"
```

---


---


## 15. Interview Q&A

**Q: Why Step Functions instead of chaining Lambda functions directly?**

Lambda functions can invoke other Lambda functions, but Step Functions adds retry logic, wait states, visual debugging, and execution history. Most critically, Transcribe is asynchronous — it takes minutes for long videos. Step Functions handles the wait state natively. A Lambda chaining approach would require polling loops and is harder to debug when something fails midway.

**Q: Why use three separate AI services instead of just Bedrock for everything?**

Rekognition is a pre-trained computer vision model — it analyzes video frames for visual content far more accurately than a general language model. Transcribe is purpose-built for accurate speech-to-text with profanity filtering. Bedrock then synthesizes both outputs with contextual reasoning. Each service is best-in-class for its modality. Using only Bedrock would require sending raw video data, which it cannot process directly.

**Q: How does the pipeline handle a 2-hour movie upload?**

Lambda has a 15-minute maximum timeout, but the Transcribe job runs asynchronously outside Lambda. Lambda starts the job and returns the job ID. Step Functions waits (using a Wait state), then a subsequent Lambda polls for completion. The actual Transcribe processing happens in AWS infrastructure — Lambda is only involved at the start and end. For very long videos, the wait time is configured accordingly.

**Q: What happens if Bedrock returns UNSAFE — does the video get deleted?**

The pipeline stores the verdict in DynamoDB and sets `review_required: true`. It sends an SNS alert to the content team. The video is not automatically deleted — a human reviews the AI decision before any destructive action. This prevents false positives from blocking legitimate content. The AI flags, humans decide on edge cases.

**Q: Why DynamoDB over RDS for storing verdicts?**

The access pattern here is simple key-value: "get verdict for this video name." DynamoDB handles this in milliseconds with no schema to manage. The AI output structure varies — Bedrock might return different fields for different content. DynamoDB's schema-flexible nature accommodates this. RDS would require migrations every time the AI output format changes.

---


## Skills Demonstrated

```
Generative AI        Amazon Bedrock, Amazon Titan, prompt engineering
Computer Vision      AWS Rekognition content moderation
Speech Recognition   AWS Transcribe, async job management
Pipeline Orchestration  AWS Step Functions, wait states, retry logic
Event-Driven Design  S3 → EventBridge → Step Functions → Lambda
Serverless           Lambda (Python 3.12), zero server management
NoSQL Design         DynamoDB schema design for variable AI outputs
IAM Security         Least-privilege roles, service-to-service auth
Monitoring           CloudWatch Logs, Step Functions execution tracing
Real-World Context   Production content moderation at streaming scale
```

---
