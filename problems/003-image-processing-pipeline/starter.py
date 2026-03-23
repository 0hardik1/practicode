import io
import json
import os

import requests
from PIL import Image, ImageOps


def main() -> None:
    image_base = os.environ["IMAGE_SERVICE_URL"]

    # TODO: process each image and upload it back to the service.
    payload = {"status": "success", "processed_count": 0}
    print(json.dumps(payload))


if __name__ == "__main__":
    main()

