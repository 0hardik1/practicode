import json
import os

import requests


def main() -> None:
    test_input = json.loads(os.environ.get("TEST_INPUT", "{}"))
    oauth_base = os.environ["OAUTH_SERVER_URL"]
    data_base = os.environ["DATA_API_URL"]

    # TODO: request a token, fetch items, transform them, POST the result, print JSON.
    response = {
        "status": "success",
        "filtered_count": 0,
        "total_value": 0,
        "item_names": [],
    }
    requests.post(f"{data_base}/data/results", json=response, timeout=5)
    print(json.dumps(response))


if __name__ == "__main__":
    main()

