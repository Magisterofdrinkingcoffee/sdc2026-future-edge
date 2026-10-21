"""RunPod handler (from the official SDC submission template).

Future Edge does not currently use GPUs – scoring is lightweight arithmetic and
any LLM is called through an API. If the team later adds GPU work (fine-tuning,
self-hosted model inference), it MUST run on RunPod and be documented here with
the Pod ID / Serverless endpoint, GPU type and runtime (hackathon rule).
"""


def handler(event):
    return {"status": "not used", "input": event.get("input")}
