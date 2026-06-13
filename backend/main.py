from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
import re

app = FastAPI()

# Simple in-memory agent registry (demo only)
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, Response
import re
from datetime import datetime
from typing import List, Dict, Any
import time
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from .brain import brain

app = FastAPI()

# Simple in-memory agent registry and event log (demo only)
connected_agents: List[str] = []
events: List[Dict[str, Any]] = []

# Prometheus metrics
AGENTS_GAUGE = Gauge('agentmink_connected_agents', 'Number of connected agents')
PII_COUNTER = Counter('agentmink_pii_events_total', 'Number of PII detection events')
MCP_REQUESTS = Counter('agentmink_mcp_requests_total', 'Total requests to /mcp', ['status'])
MCP_LATENCY = Histogram('agentmink_mcp_latency_seconds', 'Latency of /mcp requests')

PII_EMAIL = re.compile(r"[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+")
PII_PHONE = re.compile(r"\b\+?\d[\d\s\-()]{7,}\b")


def now_iso() -> str:
        return datetime.utcnow().isoformat() + "Z"


def redact_pii(text: str) -> str:
        text = PII_EMAIL.sub("[REDACTED_EMAIL]", text)
        text = PII_PHONE.sub("[REDACTED_PHONE]", text)
        return text


def log_event(event_type: str, payload: Dict[str, Any]):
        e = {"ts": now_iso(), "type": event_type, "payload": payload}
        events.insert(0, e)


@app.get("/health")
async def health():
        return {"status": "ok"}


@app.post("/mcp/register")
async def register_agent(agent_id: str):
        if agent_id not in connected_agents:
                connected_agents.append(agent_id)
    AGENTS_GAUGE.set(len(connected_agents))
    log_event("register", {"agent_id": agent_id})
        return {"registered": True, "agent_id": agent_id}


@app.post("/mcp")
async def mcp_receive(request: Request):
    start = time.time()
    payload = await request.json()
    # Expecting {'agent_id': str, 'content': str}
    agent_id = payload.get("agent_id")
    content = payload.get("content", "")
    sanitized = redact_pii(content)
    pii_detected = sanitized != content
    if pii_detected:
        PII_COUNTER.inc()
    duration = time.time() - start
    MCP_LATENCY.observe(duration)
    MCP_REQUESTS.labels(status='200').inc()
    log_event("mcp_receive", {"agent_id": agent_id, "pii_detected": pii_detected, "original_len": len(content), "latency": duration})
    return JSONResponse({"agent_id": agent_id, "sanitized": sanitized, "pii_detected": pii_detected})


@app.post("/ingest/file")
async def ingest_file(file: UploadFile = File(...)):
    contents = (await file.read()).decode(errors="ignore")
    sanitized = redact_pii(contents)
    # persist to brain (index + store)
    doc_id = brain.persist_document(file.filename, contents, sanitized)
    # count if PII detected in file (simple heuristic)
    if sanitized != contents:
        PII_COUNTER.inc()
    log_event("ingest_file", {"filename": file.filename, "size": len(contents), "doc_id": doc_id})
    return {"filename": file.filename, "sanitized_preview": sanitized[:1000], "size": len(contents), "doc_id": doc_id}


@app.get("/search")
async def search(q: str, topk: int = 5):
    results = brain.search(q, topk=topk)
    return {"results": results}


@app.get("/api/agents")
async def api_agents():
    AGENTS_GAUGE.set(len(connected_agents))
    return {"agents": connected_agents}


@app.get("/api/events")
async def api_events(limit: int = 50):
        return {"events": events[:limit]}


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
        html = f"""
        <html>
            <head>
                <title>AgentMink Dashboard (demo)</title>
                <meta charset="utf-8" />
            </head>
            <body>
                <h1>AgentMink Dashboard (demo)</h1>
                <div>
                    <strong>Connected agents</strong>
                    <ul id="agents"></ul>
                </div>
                <div>
                    <strong>Recent events</strong>
                    <table border="1" id="events">
                        <thead><tr><th>ts</th><th>type</th><th>payload</th></tr></thead>
                        <tbody></tbody>
                    </table>
                </div>
                <p id="notice"></p>

                <script>
                    async function fetchJson(path) {
                        const r = await fetch(path);
                        return r.json();
                    }

                    async function refresh() {
                        const a = await fetchJson('/api/agents');
                        const agentsUl = document.getElementById('agents');
                        agentsUl.innerHTML = '';
                        for (const ag of a.agents) {
                            const li = document.createElement('li'); li.textContent = ag; agentsUl.appendChild(li);
                        }

                        const ev = await fetchJson('/api/events');
                        const tbody = document.querySelector('#events tbody');
                        tbody.innerHTML = '';
                        for (const e of ev.events.slice(0,20)) {
                            const tr = document.createElement('tr');
                            const td1 = document.createElement('td'); td1.textContent = e.ts; tr.appendChild(td1);
                            const td2 = document.createElement('td'); td2.textContent = e.type; tr.appendChild(td2);
                            const td3 = document.createElement('td'); td3.textContent = JSON.stringify(e.payload); tr.appendChild(td3);
                            tbody.appendChild(tr);
                        }

                        // show confirmation notice if recent registration or mcp_receive exists
                        if (ev.events.length>0) {
                            const last = ev.events[0];
                            document.getElementById('notice').textContent = `Last event: ${last.type} @ ${last.ts}`;
                        }
                    }

                    setInterval(refresh, 1500);
                    refresh();
                </script>
            </body>
        </html>
        """
        return html


if __name__ == "__main__":
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
