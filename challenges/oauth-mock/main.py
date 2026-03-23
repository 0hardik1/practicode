from __future__ import annotations

import os
import secrets
import time

from fastapi import FastAPI, HTTPException, Request


CLIENT_ID = os.environ.get("CLIENT_ID", "practicode-client")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET", "practicode-secret")
TOKEN_TTL_SECONDS = int(os.environ.get("TOKEN_TTL_SECONDS", "300"))
SCOPES = os.environ.get("SCOPES", "items:read data:write").split()
TOKENS: dict[str, float] = {}

app = FastAPI(title="PractiCode OAuth Mock")


@app.get("/healthz")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/oauth/.well-known")
async def openid_configuration() -> dict[str, object]:
    return {
        "token_endpoint": "/oauth/token",
        "token_validation_endpoint": "/oauth/validate",
        "grant_types_supported": ["client_credentials"],
        "scopes_supported": SCOPES,
    }


@app.post("/oauth/token")
async def issue_token(request: Request) -> dict[str, object]:
    content_type = request.headers.get("content-type", "")
    payload = await request.json() if "application/json" in content_type else dict(await request.form())

    if payload.get("grant_type", "client_credentials") != "client_credentials":
        raise HTTPException(status_code=400, detail="Unsupported grant_type")
    if payload.get("client_id") != CLIENT_ID or payload.get("client_secret") != CLIENT_SECRET:
        raise HTTPException(status_code=401, detail="Invalid client credentials")

    token = secrets.token_urlsafe(24)
    TOKENS[token] = time.time() + TOKEN_TTL_SECONDS
    return {
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": TOKEN_TTL_SECONDS,
        "scope": " ".join(SCOPES),
    }


@app.get("/oauth/validate")
async def validate_token(request: Request, token: str | None = None) -> dict[str, object]:
    auth_header = request.headers.get("authorization", "")
    candidate = token
    if auth_header.lower().startswith("bearer "):
        candidate = auth_header.split(" ", 1)[1]

    if not candidate:
        raise HTTPException(status_code=400, detail="Missing token")

    expires_at = TOKENS.get(candidate)
    if not expires_at or expires_at <= time.time():
        raise HTTPException(status_code=401, detail="Token is invalid or expired")

    return {"active": True, "expires_at": expires_at}

