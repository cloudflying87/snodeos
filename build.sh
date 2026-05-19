#!/usr/bin/env bash
# build.sh — Brainerd Snodeos setup script
#
# Usage:
#   ./build.sh            # local dev: install, migrate, seed, run server
#   ./build.sh --docker   # Docker: build + start all services
#   ./build.sh --seed     # just (re)seed the database
#   ./build.sh --check    # run Django system checks only

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()    { echo -e "${BLUE}[snodeos]${NC} $1"; }
success() { echo -e "${GREEN}[snodeos]${NC} $1"; }
warn()    { echo -e "${YELLOW}[snodeos]${NC} $1"; }
error()   { echo -e "${RED}[snodeos]${NC} $1"; exit 1; }

MODE="${1:-}"

# ── Docker mode ────────────────────────────────────────────────────────────────
if [ "$MODE" = "--docker" ]; then
  command -v docker >/dev/null 2>&1 || error "Docker not found. Install Docker Desktop and try again."

  info "Building Docker images..."
  docker compose build

  info "Starting services (web + db + nginx)..."
  docker compose up -d

  info "Waiting for database to be ready..."
  sleep 5

  info "Running migrations..."
  docker compose exec web python3 manage.py migrate --noinput

  info "Seeding initial data..."
  docker compose exec web python3 manage.py seed_data

  info "Collecting static files..."
  docker compose exec web python3 manage.py collectstatic --noinput

  echo ""
  success "Docker stack is up!"
  echo ""
  echo "  Site:         http://snodeos.flyhomemnlab.com  (or http://localhost)"
  echo "  Admin panel:  http://localhost/admin/"
  echo ""
  warn "To create a superuser (officer/admin account):"
  echo "  docker compose exec web python3 manage.py createsuperuser"
  echo ""
  warn "To view logs:"
  echo "  docker compose logs -f web"
  echo ""
  warn "To stop:"
  echo "  docker compose down"
  exit 0
fi

# ── Seed-only mode ─────────────────────────────────────────────────────────────
if [ "$MODE" = "--seed" ]; then
  PYTHON=$(find_python)
  info "Seeding database..."
  $PYTHON manage.py seed_data
  success "Seed data applied."
  exit 0
fi

# ── Check mode ─────────────────────────────────────────────────────────────────
if [ "$MODE" = "--check" ]; then
  PYTHON=$(find_python)
  info "Running Django system checks..."
  $PYTHON manage.py check
  success "All checks passed."
  exit 0
fi

# ── Local dev mode (default) ───────────────────────────────────────────────────

find_python() {
  if [ -f "venv/bin/python3" ]; then
    echo "venv/bin/python3"
  elif command -v python3 >/dev/null 2>&1; then
    echo "python3"
  else
    error "Python 3 not found. Install it and try again."
  fi
}

PYTHON=$(find_python)

# 1. Virtual environment
if [ ! -d "venv" ]; then
  info "Creating virtual environment..."
  python3 -m venv venv
  success "Virtual environment created."
else
  info "Virtual environment already exists."
fi

PYTHON="venv/bin/python3"
PIP="venv/bin/pip"

# 2. Dependencies
info "Installing dependencies..."
$PIP install --quiet --upgrade pip
$PIP install --quiet -r requirements.txt
success "Dependencies installed."

# 3. .env file
if [ ! -f ".env" ]; then
  warn ".env not found — copying from .env.example"
  cp .env.example .env
  warn "Please review and update .env before going to production!"
else
  info ".env file found."
fi

# 4. Migrations
info "Running database migrations..."
$PYTHON manage.py migrate --noinput
success "Migrations applied."

# 5. Static files
info "Collecting static files..."
$PYTHON manage.py collectstatic --noinput --quiet
success "Static files collected."

# 6. Seed data
info "Seeding initial data (officers, stats, sponsors, announcements)..."
$PYTHON manage.py seed_data
success "Seed data applied."

# 7. System check
info "Running Django system checks..."
$PYTHON manage.py check --quiet
success "All checks passed."

# 8. Superuser prompt
echo ""
warn "Do you want to create a superuser (admin/officer account)? [y/N]"
read -r CREATE_SUPER
if [[ "$CREATE_SUPER" =~ ^[Yy]$ ]]; then
  $PYTHON manage.py createsuperuser
fi

# 9. Start dev server
echo ""
success "Build complete! Starting development server..."
echo ""
echo "  Site:         http://127.0.0.1:8000"
echo "  Admin panel:  http://127.0.0.1:8000/admin/"
echo "  Join form:    http://127.0.0.1:8000/accounts/register/"
echo "  Members:      http://127.0.0.1:8000/members/dashboard/"
echo ""
$PYTHON manage.py runserver
