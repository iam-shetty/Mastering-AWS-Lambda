import boto3
import json
import re
import urllib.request

transcribe = boto3.client("transcribe")
bedrock    = boto3.client("bedrock-runtime")

BAD_WORDS = ["sex", "nude", "fuck", "porn"]

def lambda_handler(event, context):
    job_name = event["job_name"]

    job    = transcribe.get_transcription_job(TranscriptionJobName=job_name)
    status = job["TranscriptionJob"]["TranscriptionJobStatus"]

    # Fix 1 — separate IN_PROGRESS from FAILED
    if status in ("QUEUED", "IN_PROGRESS"):
        raise Exception("RETRY: Transcription still running")

    if status == "FAILED":
        reason = job["TranscriptionJob"].get("FailureReason", "unknown")
        raise Exception(f"FAILED: Transcription job failed — {reason}")

    # COMPLETED — safe to continue
    transcript_uri = job["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]

    with urllib.request.urlopen(transcript_uri) as r:
        transcript_json = json.loads(r.read())

    transcript_text = transcript_json["results"]["transcripts"][0]["transcript"]

    # Fix 2 — word boundary matching instead of substring
    lower_text = transcript_text.lower()
    is_unsafe  = any(
        re.search(rf"\b{word}\b", lower_text)
        for word in BAD_WORDS
    )

    if is_unsafe:
        return {
            **event,
            "summary": "Blocked due to unsafe content",
            "status":  "UNSAFE"
        }

    # Fix 3 — use Rekognition labels in Bedrock prompt
    unique_labels = event.get("unique_labels", [])
    label_text    = ", ".join(unique_labels) if unique_labels else "None"

    # Fix 4 — truncate transcript to avoid Titan token limit
    transcript_cut = transcript_text[:4000]

    prompt = f"""You are a content moderator for a video platform.

Visual content detected: {label_text}

Audio transcript:
{transcript_cut}

Respond ONLY in this JSON format:
{{"status": "SAFE", "summary": "two sentence summary here"}}"""

    # Fix 5 — handle Bedrock response safely
    try:
        response = bedrock.invoke_model(
            modelId="amazon.titan-text-express-v1",
            body=json.dumps({
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": 300,
                    "temperature":   0.1,
                    "topP":          0.9
                }
            })
        )

        result   = json.loads(response["body"].read())
        ai_text  = result["results"][0]["outputText"].strip()

        # Fix 6 — Bedrock does not always return valid JSON
        try:
            verdict = json.loads(ai_text)
            summary = verdict.get("summary", ai_text)
        except json.JSONDecodeError:
            summary = ai_text[:300]

    except Exception as e:
        print(f"Bedrock failed: {e}")
        summary = transcript_cut[:200]

    return {
        **event,
        "summary": summary,
        "status":  "SAFE"
    }