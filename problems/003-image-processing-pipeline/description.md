# Image Processing Pipeline

The image service exposes a small set of source images.

Your script must:

1. Fetch the image list from `IMAGE_SERVICE_URL/images/list`.
2. Download each image.
3. Resize it to `256x256`.
4. Convert it to grayscale.
5. Add a `2px` red border.
6. Upload the transformed image back to the service.
7. Print `{"status": "success", "processed_count": <count>}`.

