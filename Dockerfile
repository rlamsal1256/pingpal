FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir setuptools && pip install --no-cache-dir -e .

COPY src/ src/

ENV PORT=8080
EXPOSE 8080

CMD uvicorn pingpal.main:app --host 0.0.0.0 --port $PORT
