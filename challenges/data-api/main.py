from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException


DATASET = [
    {"id": "1", "name": "alpha", "status": "active", "value": 10, "category": "infra", "email": "alpha@example.com", "joined_at": "2026-01-02"},
    {"id": "2", "name": "beta", "status": "inactive", "value": 5, "category": "infra", "email": "beta@example.com", "joined_at": "2026/01/05"},
    {"id": "3", "name": "gamma", "status": "active", "value": 15, "category": "data", "email": "gamma@example.com", "joined_at": "01-06-2026"},
    {"id": "4", "name": "delta", "status": "active", "value": 21, "category": "infra", "email": "delta@example.com", "joined_at": "2026-01-07T10:00:00"},
    {"id": "5", "name": None, "status": "active", "value": 12, "category": "data", "email": "gamma@example.com", "joined_at": "2026-01-07"},
    {"id": "6", "name": "theta", "status": "active", "value": 30, "category": "ops", "email": "theta@practicode.dev", "joined_at": "2026-01-08"},
    {"id": "7", "name": "iota", "status": "inactive", "value": 9, "category": "ops", "email": "iota@practicode.dev", "joined_at": "2026-01-09"},
    {"id": "8", "name": "lambda", "status": "active", "value": 8, "category": "infra", "email": "lambda@example.com", "joined_at": "2026-01-10"},
]

EXPECTED_RESULTS = {
    "oauth-visible-basic": {
        "status": "success",
        "filtered_count": 5,
        "total_value": 84,
        "item_names": ["ALPHA", "DELTA", "GAMMA", "LAMBDA", "THETA"],
    },
    "oauth-hidden-category": {
        "status": "success",
        "filtered_count": 3,
        "total_value": 39,
        "item_names": ["ALPHA", "DELTA", "LAMBDA"],
    },
    "data-visible-pagination": {
        "status": "success",
        "unique_records": 7,
        "active_records": 5,
        "domains": ["example.com", "practicode.dev"],
        "null_name_count": 1,
    },
    "data-hidden-small-pages": {
        "status": "success",
        "unique_records": 7,
        "active_records": 5,
        "domains": ["example.com", "practicode.dev"],
        "null_name_count": 1,
    },
}

LAST_POSTED_RESULT: Any = None
app = FastAPI(title="PractiCode Data API")


@app.get("/healthz")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/data/items")
async def list_items(page: int = 1, page_size: int = 50) -> dict[str, Any]:
    page = max(page, 1)
    page_size = max(page_size, 1)
    start = (page - 1) * page_size
    end = start + page_size
    items = DATASET[start:end]
    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": len(DATASET),
        "has_more": end < len(DATASET),
    }


@app.get("/data/items/{item_id}")
async def get_item(item_id: str) -> dict[str, Any]:
    for item in DATASET:
        if item["id"] == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")


@app.post("/data/results")
async def post_results(payload: Any) -> dict[str, bool]:
    global LAST_POSTED_RESULT
    LAST_POSTED_RESULT = payload
    return {"stored": True}


@app.get("/data/results")
async def get_results() -> dict[str, Any]:
    return {"payload": LAST_POSTED_RESULT}


@app.get("/data/results/validate")
async def validate_results(test_id: str) -> dict[str, Any]:
    expected = EXPECTED_RESULTS.get(test_id)
    if expected is None:
        raise HTTPException(status_code=404, detail="Unknown test id")

    passed = LAST_POSTED_RESULT == expected
    return {
        "passed": passed,
        "message": "Validation succeeded." if passed else "Posted result did not match expected payload.",
        "actual": LAST_POSTED_RESULT,
        "expected": expected,
    }

