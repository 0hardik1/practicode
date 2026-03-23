FROM python:3.12-slim

WORKDIR /app

COPY api-server/requirements.txt ./requirements.txt
COPY runner-python/requirements.txt /tmp/runner-requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r /tmp/runner-requirements.txt

COPY api-server/app ./app
COPY problems ./problems

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
