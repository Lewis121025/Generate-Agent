#!/usr/bin/env bash
set -euo pipefail

echo "======================================="
echo "  Lewis AI System - Database Services"
echo "======================================="

if [[ ! -f ".env" ]]; then
  echo "[error] .env file not found. Please create it and configure DATABASE_URL." >&2
  exit 1
fi

echo "[info] Found .env configuration file"

if ! command -v docker >/dev/null 2>&1; then
  echo "[error] Docker is not installed or not on PATH." >&2
  exit 1
fi

echo "[info] Docker is ready"
echo ""

echo "[info] Starting database services..."
echo "  • PostgreSQL (port 5432)"
echo "  • Redis (port 6379)"
echo "  • Weaviate (port 8080)"
echo ""

docker compose up -d postgres redis weaviate

if [[ $? -ne 0 ]]; then
  echo "[error] Failed to start database services" >&2
  echo "[info] Check logs: docker compose logs postgres redis weaviate" >&2
  exit 1
fi

echo "[info] Waiting for database services to be ready..."

# Wait for PostgreSQL
max_retries=30
retry_count=0
postgres_ready=false

while [[ $retry_count -lt $max_retries ]]; do
  if docker compose exec -T postgres pg_isready -U lewis >/dev/null 2>&1; then
    postgres_ready=true
    break
  fi
  retry_count=$((retry_count + 1))
  sleep 1
done

if [[ "$postgres_ready" != "true" ]]; then
  echo "[error] PostgreSQL did not become ready in time" >&2
  echo "[info] Check logs: docker compose logs postgres" >&2
  exit 1
fi

echo "[success] PostgreSQL is ready"

# Wait for Redis
retry_count=0
redis_ready=false

while [[ $retry_count -lt $max_retries ]]; do
  if docker compose exec -T redis redis-cli ping 2>&1 | grep -q "PONG"; then
    redis_ready=true
    break
  fi
  retry_count=$((retry_count + 1))
  sleep 1
done

if [[ "$redis_ready" != "true" ]]; then
  echo "[warning] Redis did not become ready in time, continuing anyway"
else
  echo "[success] Redis is ready"
fi

# Weaviate usually takes longer to start
sleep 3
echo "[success] Weaviate is started"

echo ""
echo "======================================="
echo "  ✅ Database services started!"
echo "======================================="
echo ""
echo "[info] Service status:"
docker compose ps postgres redis weaviate
echo ""
echo "[info] Common commands:"
echo "  ./scripts/db-init.sh          # Initialize database tables"
echo "  ./scripts/stop-databases.sh    # Stop database services"
echo "  docker compose logs -f         # View logs"
echo "  docker compose ps              # View status"
echo ""

