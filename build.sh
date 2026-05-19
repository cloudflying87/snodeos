#!/usr/bin/env bash
# build.sh — Brainerd Snodeos deployment script
#
# Usage:
#   ./build.sh        # Pull, rebuild images, migrate, seed, start all services
#   ./build.sh -n     # Quick restart — skip rebuild (no code changes)
#   ./build.sh -g     # Deploy local changes — skip git pull, rebuild images
#   ./build.sh -s     # Re-seed database only (containers must be running)
#   ./build.sh -c     # Run Django system checks only

set -e

REBUILD=true
SKIP_GIT_PULL=false
SEED_ONLY=false
CHECK_ONLY=false

while getopts "ngsc" opt; do
  case $opt in
    n) REBUILD=false ;;
    g) SKIP_GIT_PULL=true ;;
    s) SEED_ONLY=true ;;
    c) CHECK_ONLY=true ;;
    *)
      echo "Usage: $0 [-n] [-g] [-s] [-c]"
      echo "  -n  No rebuild (skip image rebuild — just restart containers)"
      echo "  -g  Skip git pull (deploy local changes)"
      echo "  -s  Seed database only (containers must already be running)"
      echo "  -c  Run Django system checks only"
      echo ""
      echo "Examples:"
      echo "  $0        # Full deploy: pull code, rebuild, migrate, seed, start"
      echo "  $0 -n     # Quick restart with no code changes"
      echo "  $0 -g     # Deploy local uncommitted changes"
      exit 1
      ;;
  esac
done

echo "╔════════════════════════════════════════════════════════════╗"
echo "║           Brainerd Snodeos — Build & Deploy                ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

command -v docker >/dev/null 2>&1 || { echo "❌ Docker not found. Install Docker and try again."; exit 1; }

# ── Seed-only mode ─────────────────────────────────────────────────────────────
if [ "$SEED_ONLY" = true ]; then
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Seeding database..."
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  docker compose exec web python3 manage.py seed_data
  echo "✅ Seed data applied."
  exit 0
fi

# ── Check-only mode ────────────────────────────────────────────────────────────
if [ "$CHECK_ONLY" = true ]; then
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Running Django system checks..."
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  docker compose exec web python3 manage.py check
  echo "✅ All checks passed."
  exit 0
fi

# ── PHASE 0: .env ──────────────────────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PHASE 0: Environment"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "⚠️  .env not found — copied from .env.example."
  echo "   Edit .env with real values before continuing."
  exit 1
fi
# Export .env into the shell so DB credentials are available to host-side
# commands (pg_dump, the schema-empty check). docker-compose already reads
# .env on its own for the containers.
set -a
. ./.env
set +a
echo "✅ .env found"
echo ""

# ── PHASE 1: Tear down ─────────────────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PHASE 1: Stopping Services"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

docker compose down
echo "✅ Services stopped"
echo ""

# ── PHASE 2: Git pull ──────────────────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PHASE 2: $([ "$SKIP_GIT_PULL" = true ] && echo "Using Current Code (Skipping Git Pull)" || echo "Pulling Latest Code")"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$SKIP_GIT_PULL" = false ]; then
  CURRENT_BRANCH=$(git branch --show-current)
  echo "Branch: $CURRENT_BRANCH"
  git pull origin "$CURRENT_BRANCH"
  echo "✅ Code updated"
else
  echo "⚠️  Skipping git pull — using local code"
fi
echo ""

# ── PHASE 2: Build images ──────────────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PHASE 3: $([ "$REBUILD" = true ] && echo "Rebuilding Docker Images" || echo "Using Existing Images (No Rebuild)")"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$REBUILD" = true ]; then
  echo "Build options:"
  echo "  Git pull:       $([ "$SKIP_GIT_PULL" = false ] && echo "YES" || echo "SKIPPED")"
  echo "  Rebuild images: YES"
  echo ""
  docker compose build --no-cache web nginx
  echo "✅ Images rebuilt"
else
  echo "⚠️  Using existing images — code changes not included"
  echo "   Run without -n to deploy code changes"
fi
echo ""

# ── PHASE 3: Database ──────────────────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PHASE 4: Database"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Starting database..."
docker compose up -d db
echo "Waiting for database to be ready..."
until docker compose exec db pg_isready -U "${POSTGRES_USER:-snodeos}" > /dev/null 2>&1; do
  sleep 1
done
echo "✅ Database ready"

# ── Snapshot before migrations ────────────────────────────────────────────────
# A bad migration is easier to recover from with a dump than without one.
# Dumps are kept on the host in ./backups/, last 10 retained.
BACKUP_DIR="$(pwd)/backups"
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/snodeos-$(date +%Y%m%d-%H%M%S).sql.gz"

# Skip on fresh install (no tables yet) — pg_dump still succeeds but file is empty
if docker compose exec -T db psql -U "${POSTGRES_USER:-snodeos}" -d "${POSTGRES_DB:-snodeos}" -tAc "SELECT 1 FROM pg_tables WHERE schemaname='public' LIMIT 1" 2>/dev/null | grep -q 1; then
  echo "Snapshotting database to $BACKUP_FILE..."
  docker compose exec -T db pg_dump -U "${POSTGRES_USER:-snodeos}" -d "${POSTGRES_DB:-snodeos}" --no-owner --no-privileges 2>/dev/null | gzip > "$BACKUP_FILE"
  if [ -s "$BACKUP_FILE" ]; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "✅ Backup saved ($SIZE)"
    # Prune to last 10 dumps
    ls -1t "$BACKUP_DIR"/snodeos-*.sql.gz 2>/dev/null | tail -n +11 | xargs -r rm -f
  else
    echo "⚠️  Backup file is empty — pg_dump may have failed. Continuing anyway."
    rm -f "$BACKUP_FILE"
  fi
else
  echo "ℹ️  Fresh install — no existing tables to back up"
fi
echo ""

echo "Running migrations..."
docker compose run --rm web python3 manage.py migrate --noinput
echo "✅ Migrations complete"
echo ""

# ── PHASE 4: Static files ──────────────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PHASE 5: Static Files"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

docker compose run --rm web python3 manage.py collectstatic --noinput --verbosity 1
echo "✅ Static files collected"
echo ""

# ── PHASE 5: Seed data ─────────────────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PHASE 6: Seed Data"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

docker compose run --rm web python3 manage.py seed_data
echo "✅ Seed data applied"
echo ""

# ── PHASE 6: Start services ────────────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PHASE 7: Starting Services"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

docker compose up -d
echo "Waiting for services to be healthy..."
sleep 8

if docker compose ps | grep -q "healthy"; then
  echo "✅ Services are healthy"
else
  echo "⚠️  Services may still be starting — check with: docker compose ps"
fi
echo ""

# ── Summary ────────────────────────────────────────────────────────────────────
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                  DEPLOYMENT COMPLETE!                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "  Site:              https://snodeos.flyhomemnlab.com"
echo "  Management panel:  https://snodeos.flyhomemnlab.com/manage/"
echo "  Django admin:      https://snodeos.flyhomemnlab.com/admin/"
echo ""
echo "  To create a superuser:"
echo "    docker compose exec web python3 manage.py createsuperuser"
echo ""
echo "  To view logs:  docker compose logs -f web"
echo "  To stop:       docker compose down"
echo ""
echo "Build completed: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo ""
