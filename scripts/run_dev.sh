#!/bin/bash
# Initialize development environment for Amdrodd Lead Scorer

echo "--- Initializing ALS Environment ---"

# 1. Start Infrastructure
echo "Starting Docker containers..."
docker-compose up -d

# 2. Wait for Postgres to be ready
echo "Waiting for PostgreSQL (pgvector)..."
until docker exec als-postgres pg_isready -U admin -d lead_scorer_db > /dev/null 2>&1; do
  sleep 1
done
echo "PostgreSQL is live!"

# 3. Install dependencies
echo "Installing Poetry dependencies..."
poetry install

# 4. Copy template if .env doesn't exist
if [ ! -f .env ]; then
  echo "Initializing .env from template..."
  cp .env.template .env
fi

echo "--- Environment Ready! ---"
echo "Run: 'poetry run streamlit run management_dashboard/app.py' to start the dashboard."
echo "Run: 'poetry run pytest tests/test_infrastructure.py' to verify the stack."
