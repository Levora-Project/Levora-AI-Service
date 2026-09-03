FROM python:3.12-slim as builder

WORKDIR /tmp
RUN pip install poetry poetry-plugin-export
COPY ./pyproject.toml ./poetry.lock* /tmp/
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM python:3.12-slim

WORKDIR /app
COPY --from=builder /tmp/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy Prisma schema and generate the client
COPY ./prisma /app/prisma
RUN prisma generate

# Copy application source code
COPY ./src /app/src

# Expose port and run the app
CMD uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}
