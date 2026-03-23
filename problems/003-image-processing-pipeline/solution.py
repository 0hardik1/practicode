import io
import json
import os

import requests
from PIL import Image, ImageOps


def transform_image(raw_bytes: bytes) -> bytes:
    image = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
    image = image.resize((252, 252))
    image = ImageOps.grayscale(image).convert("RGB")
    image = ImageOps.expand(image, border=2, fill=(255, 0, 0))
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def main() -> None:
    image_base = os.environ["IMAGE_SERVICE_URL"]
    images = requests.get(f"{image_base}/images/list", timeout=5).json()["images"]

    for image_id in images:
        raw_bytes = requests.get(f"{image_base}/images/{image_id}", timeout=5).content
        transformed = transform_image(raw_bytes)
        requests.post(
            f"{image_base}/images/{image_id}/upload",
            files={"file": (f"{image_id}.png", transformed, "image/png")},
            timeout=10,
        ).raise_for_status()

    payload = {"status": "success", "processed_count": len(images)}
    print(json.dumps(payload))


if __name__ == "__main__":
    main()

