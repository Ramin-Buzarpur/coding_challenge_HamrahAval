FROM python:3.12-slim

# Logs must not be buffered, otherwise `kubectl logs` shows nothing until exit.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Do not run as root.
RUN useradd --create-home --uid 10001 appuser
USER appuser

ENTRYPOINT ["python", "-m", "app"]
CMD ["create", "example-group"]
