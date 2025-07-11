# Makefile for EduRPG Project

.PHONY: help build up down restart logs clean dev dev-up dev-down dev-logs

# Default target
help:
	@echo "EduRPG Docker Commands:"
	@echo "  make build     - Build all containers"
	@echo "  make up        - Start all containers in production mode"
	@echo "  make down      - Stop all containers"
	@echo "  make restart   - Restart all containers"
	@echo "  make logs      - View container logs"
	@echo "  make clean     - Remove all containers and volumes"
	@echo ""
	@echo "Development Commands:"
	@echo "  make dev       - Start in development mode with hot-reload"
	@echo "  make dev-up    - Same as 'make dev'"
	@echo "  make dev-down  - Stop development containers"
	@echo "  make dev-logs  - View development container logs"
	@echo ""
	@echo "Individual Services:"
	@echo "  make frontend  - Start only frontend"
	@echo "  make backend   - Start only backend with dependencies"
	@echo "  make db        - Start only database"

# Production commands
build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
	docker system prune -f

# Development commands
dev:
	docker-compose -f docker-compose.dev.yml up

dev-up:
	docker-compose -f docker-compose.dev.yml up -d

dev-down:
	docker-compose -f docker-compose.dev.yml down

dev-logs:
	docker-compose -f docker-compose.dev.yml logs -f

# Individual services
frontend:
	docker-compose up frontend

backend:
	docker-compose up backend db redis

db:
	docker-compose up db

# Database commands
db-backup:
	docker exec edurpg-db pg_dump -U postgres edurpg > backup_$(shell date +%Y%m%d_%H%M%S).sql

db-restore:
	@echo "Usage: make db-restore FILE=backup.sql"
	docker exec -i edurpg-db psql -U postgres edurpg < $(FILE)

# Utility commands
shell-frontend:
	docker exec -it edurpg-frontend sh

shell-backend:
	docker exec -it edurpg-backend bash

shell-db:
	docker exec -it edurpg-db psql -U postgres edurpg

# Health check
health:
	@echo "Checking service health..."
	@curl -f http://localhost:3000 > /dev/null 2>&1 && echo "✓ Frontend is running" || echo "✗ Frontend is not running"
	@curl -f http://localhost:8000/health > /dev/null 2>&1 && echo "✓ Backend is running" || echo "✗ Backend is not running"
	@docker exec edurpg-db pg_isready > /dev/null 2>&1 && echo "✓ Database is running" || echo "✗ Database is not running"
	@docker exec edurpg-redis redis-cli ping > /dev/null 2>&1 && echo "✓ Redis is running" || echo "✗ Redis is not running"