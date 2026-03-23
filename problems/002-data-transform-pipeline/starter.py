import json
import os

import requests


def main() -> None:
    test_input = json.loads(os.environ.get("TEST_INPUT", "{}"))
    data_base = os.environ["DATA_API_URL"]
    page_size = test_input.get("page_size", 3)

    # TODO: fetch all pages, clean the records, and post the summary.
    payload = {
        "status": "success",
        "unique_records": 0,
        "active_records": 0,
        "domains": [],
        "null_name_count": 0,
    }
    requests.post(f"{data_base}/data/results", json=payload, timeout=5)
    print(json.dumps(payload))


if __name__ == "__main__":
    main()

