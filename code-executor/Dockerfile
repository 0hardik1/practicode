FROM python:3.12-slim

WORKDIR /app

COPY code-executor/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY runner-python/requirements.txt /tmp/runner-requirements.txt
RUN pip install --no-cache-dir -r /tmp/runner-requirements.txt

COPY code-executor/app ./app
COPY runner-python ./runner-python

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
