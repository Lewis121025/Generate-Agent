#!/usr/bin/env bash
set -euo pipefail

echo "======================================="
echo "  Lewis AI System - Stop Databases"
echo "======================================="

if ! command -v docker >/dev/null 2>&1; then
  echo "[error] Docker is not installed or not on PATH." >&2
  exit 1
fi

# Check if any database services are running
running_services=$(docker compose ps postgres redis weaviate --format json 2>/dev/null | grep -o '"State":"running"' | head -1 || echo "")

if [[ -z "$running_services" ]]; then
  echo "[info] No database services are currently running"
  exit 0
fi

echo "[info] Currently running services:"
docker compose ps postgres redis weaviate
echo ""

# Ask about volume cleanup
clean_volumes=false
read -p "Delete data volumes? This will remove all database data (y/N): " response
if [[ "$response" == "y" || "$response" == "Y" ]]; then
  clean_volumes=true
  echo "[warning] This will delete all database data!"
  read -p "Confirm deletion? Type 'yes' to continue: " confirm
  if [[ "$confirm" != "yes" ]]; then
    echo "[info] Operation cancelled"
    exit 0
  fi
fi

echo ""
echo "[info] Stopping database services..."

if [[ "$clean_volumes" == "true" ]]; then
  echo "[info] Stopping services and removing data volumes..."
  docker compose down -v postgres redis weaviate
else
  echo "[info] Stopping services (preserving data volumes)..."
  docker compose stop postgres redis weaviate
fi

if [[ $? -ne 0 ]]; then
  echo "[error] Failed to stop services" >&2
  exit 1
fi

echo ""
echo "======================================="
echo "  ✅ Database services stopped"
echo "======================================="
echo ""

if [[ "$clean_volumes" == "true" ]]; then
  echo "[info] Data volumes have been removed, all data cleared"
else
  echo "[info] Data volumes preserved, data is safe"
  echo "[info] Restart with: ./scripts/start-databases.sh"
fi

echo ""

