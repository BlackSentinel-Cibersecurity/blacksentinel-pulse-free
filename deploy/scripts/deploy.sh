#!/bin/bash
# ============================================
# BlackSentinel Pulse - Production Deploy Script
# ============================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_banner() {
    echo -e "${RED}"
    echo "  ████████╗███████╗ ██████╗ ██╗     ██╗ ██████╗ ███████╗███╗   ██╗ ██████╗██╗  ██╗"
    echo "  ╚══██╔══╝██╔════╝██╔═══██╗██║     ██║██╔═══██╗██╔════╝████╗  ██║██╔════╝██║  ██║"
    echo "     ██║   █████╗  ██║   ██║██║     ██║██║   ██║███████╗██╔██╗ ██║██║     ███████║"
    echo "     ██║   ██╔══╝  ██║   ██║██║     ██║██║   ██║╚════██║██║╚██╗██║██║     ██╔══██║"
    echo "     ██║   ███████╗╚██████╔╝███████╗██║╚██████╔╝███████║██║ ╚████║╚██████╗██║  ██║"
    echo "     ╚═╝   ╚══════╝ ╚═════╝ ╚══════╝╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝ ╚═════╝╚═╝  ╚═╝"
    echo -e "${NC}"
    echo -e "  ${BLUE}BlackSentinel Pulse - Production Deployment${NC}"
    echo ""
}

log() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

check_prerequisites() {
    log "Checking prerequisites..."

    command -v docker >/dev/null 2>&1 || error "Docker is not installed"
    command -v docker-compose >/dev/null 2>&1 || error "Docker Compose is not installed"

    if [ ! -f "$PROJECT_DIR/.env" ]; then
        warn ".env file not found. Creating from template..."
        cp "$PROJECT_DIR/config/envs/.env.production" "$PROJECT_DIR/.env"
        echo ""
        error "Please edit .env file with your production values before deploying."
    fi

    log "Prerequisites OK"
}

generate_secrets() {
    log "Generating secure secrets..."

    if grep -q "change-me-in-production" "$PROJECT_DIR/.env"; then
        NEW_SECRET=$(openssl rand -hex 32)
        sed -i.bak "s/change-me-in-production/$NEW_SECRET/" "$PROJECT_DIR/.env"
        rm -f "$PROJECT_DIR/.env.bak"
        log "Generated new SECRET_KEY"
    fi

    if grep -q "pulse:pulse@localhost" "$PROJECT_DIR/.env"; then
        DB_PASS=$(openssl rand -base64 32)
        sed -i.bak "s/pulse:pulse@localhost/pulse:${DB_PASS}@postgres/" "$PROJECT_DIR/.env"
        rm -f "$PROJECT_DIR/.env.bak"
        log "Generated database password"
    fi
}

deploy() {
    log "Deploying BlackSentinel Pulse..."

    cd "$PROJECT_DIR"

    log "Building Docker images..."
    docker-compose -f docker-compose.prod.yml build

    log "Starting services..."
    docker-compose -f docker-compose.prod.yml up -d

    log "Waiting for services to be ready..."
    sleep 15

    log "Running database migrations..."
    docker-compose -f docker-compose.prod.yml exec -T backend python -c "
import asyncio
from app.core.database import engine, Base
from app.models import *
async def create():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('Database tables created!')
asyncio.run(create())
" 2>/dev/null || warn "Migration step skipped (tables may already exist)"

    log "Seeding initial data..."
    docker-compose -f docker-compose.prod.yml exec -T backend python seed.py 2>/dev/null || warn "Seed step skipped"

    echo ""
    log "=========================================="
    log "  Deployment Complete!"
    log "=========================================="
    echo ""
    log "  Frontend:   http://localhost"
    log "  API Docs:   http://localhost/api/v1/../api/docs"
    log "  Grafana:    http://localhost:3001"
    echo ""
    log "  Login: admin / admin123"
    echo ""
}

status() {
    cd "$PROJECT_DIR"
    docker-compose -f docker-compose.prod.yml ps
}

logs() {
    cd "$PROJECT_DIR"
    docker-compose -f docker-compose.prod.yml logs -f --tail=100
}

stop() {
    cd "$PROJECT_DIR"
    docker-compose -f docker-compose.prod.yml down
}

case "${1:-deploy}" in
    deploy)
        print_banner
        check_prerequisites
        generate_secrets
        deploy
        ;;
    status) status ;;
    logs) logs ;;
    stop) stop ;;
    restart)
        stop
        deploy
        ;;
    *)
        echo "Usage: $0 {deploy|status|logs|stop|restart}"
        exit 1
        ;;
esac
