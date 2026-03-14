# Override these via environment variables or a local .env.local file
PROJECT    ?= waypoint-hackathon
REGION     ?= us-central1
INSTANCE   ?= waypoint-hackathon:us-central1:waypoint-db
DB_NAME    ?= waypoint
PROXY_PORT ?= 5433

# ── Local dev ────────────────────────────────────────────────────────────────

run:
	cd backend && DATABASE_URL=$$(cat ../.env | grep ^DATABASE_URL | cut -d= -f2-) uvicorn main:app --reload --port 8080

# ── Cloud SQL ────────────────────────────────────────────────────────────────

# Start the Auth Proxy (run in a separate terminal — required before seed-prod or psql-prod)
proxy:
	cloud-sql-proxy $(INSTANCE) --port=$(PROXY_PORT)

# Reseed Cloud SQL via Auth Proxy (requires proxy running in another terminal)
seed-prod:
	@echo "Seeding Cloud SQL via Auth Proxy on port $(PROXY_PORT)..."
	@CREDS=$$(gcloud secrets versions access latest --secret=waypoint-db-url --project=$(PROJECT) | sed 's|postgresql://\(.*\)@.*|\1|'); \
	DATABASE_URL="postgresql://$$CREDS@127.0.0.1:$(PROXY_PORT)/$(DB_NAME)" python backend/seed.py

# Open a psql shell to Cloud SQL (requires proxy running)
psql-prod:
	@CREDS=$$(gcloud secrets versions access latest --secret=waypoint-db-url --project=$(PROJECT) | sed 's|postgresql://\(.*\)@.*|\1|'); \
	USER=$$(echo "$$CREDS" | cut -d: -f1); \
	PASS=$$(echo "$$CREDS" | cut -d: -f2); \
	PGPASSWORD="$$PASS" psql -h 127.0.0.1 -p $(PROXY_PORT) -U $$USER $(DB_NAME)

# ── Cloud Run ────────────────────────────────────────────────────────────────

deploy:
	gcloud builds submit --config cloudbuild.yaml --project=$(PROJECT) \
		--substitutions=COMMIT_SHA=$$(git rev-parse --short HEAD)

logs:
	gcloud run services logs read waypoint --project=$(PROJECT) --region=$(REGION) --limit=100

# ── Evaluation ───────────────────────────────────────────────────────────────

eval:
	python eval_suite.py

eval-layer1:
	python eval_suite.py --layer1-only

eval-layer2:
	python eval_suite.py --layer2-only

help:
	@echo ""
	@echo "  Waypoint — available commands"
	@echo ""
	@echo "  Local dev"
	@echo "    make run          Start backend locally (uvicorn --reload)"
	@echo ""
	@echo "  Cloud SQL"
	@echo "    make proxy        Start Auth Proxy on port $(PROXY_PORT) (run in a separate terminal)"
	@echo "    make seed-prod    Reseed Cloud SQL via Auth Proxy (proxy must be running)"
	@echo "    make psql-prod    Open psql shell to Cloud SQL (proxy must be running)"
	@echo ""
	@echo "  Cloud Run"
	@echo "    make deploy       Build + deploy to Cloud Run via Cloud Build"
	@echo "    make logs         Tail Cloud Run logs (last 100 lines)"
	@echo ""
	@echo "  Evaluation"
	@echo "    make eval         Run full eval suite (Layer 1 + 2 + 2b)"
	@echo "    make eval-layer1  Tool correctness only (no API key needed)"
	@echo "    make eval-layer2  Routing tests only (no DB needed)"
	@echo ""

.PHONY: run proxy seed-prod psql-prod deploy logs eval eval-layer1 eval-layer2 help
