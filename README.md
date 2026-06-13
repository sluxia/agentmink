# agentmink
Company OS with PII Blocker that enables businesses safely interact with AI safely.

## How to use

Quick guide to run and test locally.

- Create and activate a Python venv:

	python3 -m venv .venv
	source .venv/bin/activate

- Install backend dependencies:

	pip install -r backend/requirements.txt

- Run the FastAPI backend locally:

	uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

- Ingest a file via curl (example):

	curl -F "file=@/path/to/sample.txt" http://localhost:8000/ingest/file

- Search the brain:

	curl "http://localhost:8000/search?q=your+query&topk=5"

- Run the demo client agent (optional):

	pip install -r client/requirements.txt
	python client/agent.py --agent-id demo1 --text "Hello from agent"

- Run with Docker Compose (backend + prometheus + grafana):

	docker compose up --build

Notes:
- The backend performs basic PII redaction on ingest. Persisted documents are stored in `backend/brain.db`.
- If FAISS is available in the environment it will be used for faster vector search; otherwise the implementation falls back to a brute-force vector similarity.

