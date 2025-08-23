.PHONY: api ui dev docker-up docker-down

api:
	uvicorn api_interface:app --reload --port 8000

ui:
	cd ui && npm install && npm run dev

dev:
	make -j2 api ui

docker-up:
	docker compose up --build

docker-down:
	docker compose down


