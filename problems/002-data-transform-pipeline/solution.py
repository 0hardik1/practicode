import json
import os

import requests


def main() -> None:
    test_input = json.loads(os.environ.get("TEST_INPUT", "{}"))
    data_base = os.environ["DATA_API_URL"]
    page_size = test_input.get("page_size", 3)

    items = []
    page = 1
    while True:
        response = requests.get(
            f"{data_base}/data/items",
            params={"page": page, "page_size": page_size},
            timeout=5,
        )
        response.raise_for_status()
        payload = response.json()
        items.extend(payload["items"])
        if not payload["has_more"]:
            break
        page += 1

    deduped = {}
    for item in items:
        deduped.setdefault(item["email"], item)

    unique_records = list(deduped.values())
    payload = {
        "status": "success",
        "unique_records": len(unique_records),
        "active_records": sum(1 for item in unique_records if item["status"] == "active"),
        "domains": sorted({item["email"].split("@")[1] for item in unique_records}),
        "null_name_count": sum(1 for item in items if not item["name"]),
    }
    requests.post(f"{data_base}/data/results", json=payload, timeout=5).raise_for_status()
    print(json.dumps(payload))


if __name__ == "__main__":
    main()

