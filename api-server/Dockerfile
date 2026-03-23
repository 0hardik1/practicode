FROM python:3.12-slim

WORKDIR /app

COPY api-server/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY api-server/app ./app
COPY problems ./problems

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
