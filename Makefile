.PHONY: dev backend frontend ingest install docker-up docker-down docker-ingest docker-logs

# Start both backend and frontend
dev:
	@echo "Starting backend and frontend..."
	@make backend &
	@make frontend

# Backend
backend:
	cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000

# Frontend
frontend:
	cd frontend && npm run dev

# Ingest knowledge base into ChromaDB
ingest:
	cd backend && source venv/bin/activate && python -m scripts.ingest_knowledge

# Install all dependencies
install:
	cd backend && python3.11 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
	cd frontend && npm install

# Run tests
test:
	cd backend && source venv/bin/activate && python -m pytest tests/ -v

# Docker
docker-up:
	docker compose up --build

docker-down:
	docker compose down

docker-ingest:
	docker compose run --rm ingest

docker-logs:
	docker compose logs -f
