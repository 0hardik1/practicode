from __future__ import annotations

from app.schemas import ExecutionRequest


def build_job_manifest(
    request: ExecutionRequest,
    callback_url: str,
    runner_image: str = "practicode-runner-python:latest",
) -> dict:
    short_id = request.submission_id[:8]
    env = [
        {"name": "SUBMISSION_ID", "value": request.submission_id},
        {"name": "CALLBACK_URL", "value": callback_url},
    ]
    env.extend(
        {"name": key, "value": value}
        for key, value in request.challenge_services.items()
    )

    return {
        "apiVersion": "batch/v1",
        "kind": "Job",
        "metadata": {
            "name": f"exec-{short_id}",
            "namespace": "executor",
            "labels": {
                "app": "code-execution",
                "submission-id": request.submission_id,
            },
        },
        "spec": {
            "ttlSecondsAfterFinished": 120,
            "activeDeadlineSeconds": request.time_limit_seconds + 30,
            "backoffLimit": 0,
            "template": {
                "spec": {
                    "restartPolicy": "Never",
                    "containers": [
                        {
                            "name": "runner",
                            "image": runner_image,
                            "env": env,
                            "resources": {
                                "limits": {
                                    "cpu": "1",
                                    "memory": f"{request.memory_limit_mb}Mi",
                                },
                                "requests": {
                                    "cpu": "250m",
                                    "memory": "128Mi",
                                },
                            },
                        }
                    ],
                }
            },
        },
    }

