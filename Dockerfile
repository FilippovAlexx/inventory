FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir uv
RUN uv pip install --system -r <(uv pip compile --upgrade --generate-hashes pyproject.toml) || true
# Fallback simple install if pip-tools not available in your env:
RUN pip install --no-cache-dir fastapi uvicorn[standard] sqlalchemy[asyncio] asyncpg alembic pydantic-settings python-dotenv
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]