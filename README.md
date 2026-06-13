# Akachi
Company OS with PII Blocker that enables businesses safely interact with AI safely.

## How to use

This section is written for beginners. It explains how to set up the project, start the backend, ingest a file, and search the stored documents.

### 1) Install Python and prerequisites

You need Python 3.12 installed. If you do not have Python installed, install it first for your platform.

Then create a Python virtual environment and activate it:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

If you are on Windows, use:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) Install backend dependencies

Install the Python packages needed by the backend:

```bash
pip install -r backend/requirements.txt
```

### 3) Start the backend server

Run the FastAPI server on port `8000`:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

After the server starts, open this URL in your browser to confirm it is running:

```
http://localhost:8000/health
```

You should see a simple health response like `{ "status": "ok" }`.

### 4) Create a sample file to ingest

Create a test file named `sample.txt` in the repository root:

```bash
cat > sample.txt <<'EOF'
This is a test document.
Contact: alice@example.com
Phone: +1 555 123 4567
EOF
```

### 5) Ingest the file into agentmink

Use `curl` to upload the file to the ingest endpoint:

```bash
curl -F "file=@sample.txt" http://localhost:8000/ingest/file
```

Expected response structure:

```json
{
  "filename": "sample.txt",
  "sanitized_preview": "This is a test document.\nContact: [REDACTED_EMAIL]\nPhone: [REDACTED_PHONE]",
  "size": 97,
  "doc_id": 1
}
```

This means the backend stored the file and redacted the PII.

### 6) Search the stored documents

Run the search endpoint against the saved content:

```bash
curl "http://localhost:8000/search?q=contact&topk=5"
```

Example response:

```json
{
  "results": [
    {
      "id": 1,
      "filename": "sample.txt",
      "sanitized": "This is a test document.\nContact: [REDACTED_EMAIL]\nPhone: [REDACTED_PHONE]",
      "score": 0.78
    }
  ]
}
```

### 7) Optional: Run the demo client agent

Install the client dependencies and run the demo client:

```bash
pip install -r client/requirements.txt
python client/agent.py --agent-id demo1 --text "Hello from agent"
```

This client sends a text message to the backend and shows the backend response.

### 8) Optional: Run everything with Docker Compose

If you want to run the backend plus monitoring locally, use Docker Compose:

```bash
docker compose up --build
```

This starts the backend, Prometheus, and Grafana together.

### Notes for beginners

- The backend stores documents in `backend/brain.db`.
- The `ingest/file` endpoint sanitizes personally identifiable information (PII) such as emails and phone numbers.
- The `search` endpoint performs a text-based search over the stored embeddings.
- If FAISS is installed in your environment, the project uses it for faster search; otherwise it uses a local fallback.

