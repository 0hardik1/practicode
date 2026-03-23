import json
import os

import requests


def main() -> None:
    test_input = json.loads(os.environ.get("TEST_INPUT", "{}"))
    oauth_base = os.environ["OAUTH_SERVER_URL"]
    data_base = os.environ["DATA_API_URL"]

    token_response = requests.post(
        f"{oauth_base}/oauth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": os.environ["CLIENT_ID"],
            "client_secret": os.environ["CLIENT_SECRET"],
        },
        timeout=5,
    )
    token_response.raise_for_status()
    access_token = token_response.json()["access_token"]

    items_response = requests.get(
        f"{data_base}/data/items",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=5,
    )
    items_response.raise_for_status()
    items = items_response.json()["items"]

    filtered = [item for item in items if item["status"] == "active" and item["name"]]
    category = test_input.get("category")
    if category:
        filtered = [item for item in filtered if item["category"] == category]

    payload = {
        "status": "success",
        "filtered_count": len(filtered),
        "total_value": sum(item["value"] for item in filtered),
        "item_names": sorted(item["name"].upper() for item in filtered),
    }
    requests.post(f"{data_base}/data/results", json=payload, timeout=5).raise_for_status()
    print(json.dumps(payload))


if __name__ == "__main__":
    main()

