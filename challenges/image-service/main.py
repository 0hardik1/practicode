from __future__ import annotations

from io import BytesIO

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response
from PIL import Image, ImageChops, ImageOps


app = FastAPI(title="PractiCode Image Service")
UPLOADED: dict[str, bytes] = {}


def _render_source_images() -> dict[str, bytes]:
    colors = {"img-1": "#3563d9", "img-2": "#27a376", "img-3": "#d97235"}
    rendered: dict[str, bytes] = {}
    for image_id, color in colors.items():
        image = Image.new("RGB", (320, 180), color=color)
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        rendered[image_id] = buffer.getvalue()
    return rendered


SOURCE_IMAGES = _render_source_images()


def _expected_image(image_id: str) -> Image.Image:
    source = Image.open(BytesIO(SOURCE_IMAGES[image_id])).convert("RGB")
    resized = source.resize((252, 252))
    grayscale = ImageOps.grayscale(resized).convert("RGB")
    bordered = ImageOps.expand(grayscale, border=2, fill=(255, 0, 0))
    return bordered


@app.get("/healthz")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/images/list")
async def list_images() -> dict[str, list[str]]:
    return {"images": list(SOURCE_IMAGES.keys())}


@app.get("/images/{image_id}")
async def get_image(image_id: str) -> Response:
    payload = SOURCE_IMAGES.get(image_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Image not found")
    return Response(content=payload, media_type="image/png")


@app.post("/images/{image_id}/upload")
async def upload_image(image_id: str, file: UploadFile = File(...)) -> dict[str, bool]:
    if image_id not in SOURCE_IMAGES:
        raise HTTPException(status_code=404, detail="Image not found")
    UPLOADED[image_id] = await file.read()
    return {"stored": True}


def _compare_uploaded_image(image_id: str) -> tuple[bool, str]:
    uploaded = UPLOADED.get(image_id)
    if uploaded is None:
        return False, "Image was not uploaded."

    uploaded_image = Image.open(BytesIO(uploaded)).convert("RGB")
    expected_image = _expected_image(image_id)
    if uploaded_image.size != expected_image.size:
        return False, "Uploaded image dimensions are incorrect."

    diff = ImageChops.difference(uploaded_image, expected_image)
    if diff.getbbox() is not None:
        return False, "Uploaded image pixels do not match the expected transformation."
    return True, "Validation succeeded."


@app.get("/images/{image_id}/validate")
async def validate_image(image_id: str) -> dict[str, object]:
    if image_id not in SOURCE_IMAGES:
        raise HTTPException(status_code=404, detail="Image not found")
    passed, message = _compare_uploaded_image(image_id)
    return {"passed": passed, "message": message}


@app.get("/images/validate-all")
async def validate_all() -> dict[str, object]:
    failures = []
    for image_id in SOURCE_IMAGES:
        passed, message = _compare_uploaded_image(image_id)
        if not passed:
            failures.append({"image_id": image_id, "message": message})

    return {
        "passed": not failures,
        "message": "Validation succeeded." if not failures else "One or more images failed validation.",
        "actual": {"validated_images": list(UPLOADED.keys())},
        "expected": {"validated_images": list(SOURCE_IMAGES.keys())},
        "failures": failures,
    }

