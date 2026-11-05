# LogNexus Agentic Observability

An AI-powered observability platform that uses autonomous agents, RAG (Retrieval-Augmented Generation), and LangGraph pipelines to monitor logs, correlate alerts, and perform root cause analysis (RCA) on incidents in real time.

## Architecture Overview

```
Loki (log source)
      │
      ▼
AgenticMonitorAgent        ← fetches, normalizes, detects anomalies, enriches semantically
      │  (EventBus)
      ▼
AgenticCorrelationAgent    ← groups alerts into incidents, suppresses duplicates
      │  (EventBus)
      ▼
AgenticRCAAgent            ← LLM-powered root cause analysis, RAG-assisted lookups
      │
      ▼
incidents/ + Pushover notification
      │
      ▼
Control Dashboard (Gradio) ← start/stop agents, view incidents, export reports
```

## Project Structure

```
lognexus_agentic-observability/
├── agents/              # Monitor, Correlation, RCA agents
├── pipeline/            # LangGraph pipeline (StateGraph)
├── rag/                 # FAISS-based RAG store + seeding scripts
├── dashboard/           # Gradio control dashboard
├── data/
│   ├── incidents/       # Generated incident JSON files
│   ├── exports/         # HTML and CSV exports
│   └── logs/            # Runtime logs
├── scripts/             # Helper scripts (alert generation, etc.)
├── utils/               # Shared utilities
├── main.py              # Headless agent runner (all 3 agents in parallel)
└── requirements.txt
```

## Prerequisites

- Python 3.10+
- Access to a Loki log aggregation endpoint
- OpenAI API key (for LLM-powered RCA and RAG embeddings)
- Pushover account (optional, for incident push notifications)

## Installation

### 1. Install dependencies

```bash
cd src/observability
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 2. Seed the RAG knowledge base (first time only)

```bash
python3 -m rag.seed_rag
```

## Configuration

Set the following environment variables before running:

| Variable             | Description                              | Required |
|----------------------|------------------------------------------|----------|
| `USE_LLM`            | Enable LLM-powered RCA (`true`/`false`)  | Yes      |
| `OPENAI_API_KEY`     | OpenAI API key for LLM + embeddings      | Yes      |
| `PUSHOVER_USER_KEY`  | Pushover user key for notifications      | No       |
| `PUSHOVER_APP_TOKEN` | Pushover app token for notifications     | No       |

```bash
export USE_LLM=true
export OPENAI_API_KEY=...
export PUSHOVER_USER_KEY=...
export PUSHOVER_APP_TOKEN=...
```

## Execution

### Option 1 — Control Dashboard (recommended)

Launches a Gradio UI to start/stop agents, browse incidents, and export reports.

```bash
source venv/bin/activate

export USE_LLM=true
export OPENAI_API_KEY=...
export PUSHOVER_USER_KEY=...
export PUSHOVER_APP_TOKEN=...

python3 dashboard/agentic_control_dashboard.py
```

Then open the dashboard in your browser:

```
http://localhost:7861/
```

### Option 2 — Headless Agent Runner

Runs all three agents (Monitor → Correlation → RCA) in parallel threads without a UI.

```bash
source venv/bin/activate

export USE_LLM=true
export OPENAI_API_KEY=...

python3 main.py
```

### Option 3 — LangGraph Pipeline

Runs the full pipeline as a single LangGraph `StateGraph` pass.

```bash
python3 -m pipeline.langgraph_pipeline
```

## Agents

| Agent                       | Role                                                                 |
|-----------------------------|----------------------------------------------------------------------|
| `AgenticMonitorAgent`       | Polls Loki every 30s, normalizes logs, detects anomalies, enriches semantically |
| `AgenticCorrelationAgent`   | Groups related alerts into incidents, suppresses duplicate signatures |
| `AgenticRCAAgent`           | Performs LLM + RAG-assisted root cause analysis, sends notifications |

## Alert Types

| Alert Type              | Category      |
|-------------------------|---------------|
| `ErrorSpike`            | application   |
| `TimeoutSpike`          | dependency    |
| `RareLogPattern`        | anomaly       |
| `DependencyDegradation` | dependency    |

## RAG Knowledge Base

The platform uses a FAISS vector store (via LangChain + OpenAI embeddings) to retrieve similar past incidents and improve RCA quality. Seed it with known incident/fix pairs:

```bash
python3 -m rag.seed_rag
```

The index is persisted in `rag_index/` and loaded automatically on startup.

## Outputs

- **`data/incidents/INC-<id>.json`** — full incident record with RCA
- **`data/exports/INC-<id>.html`** — human-readable incident report
- **`data/exports/INC-<id>_metrics.csv`** — metrics snapshot
- **`data/exports/INC-<id>_rca.csv`** — RCA summary table
- **Pushover notification** — real-time push alert on incident creation

## License

Internal use only — VIAVI Solutions.
