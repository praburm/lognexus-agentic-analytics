# LogNexus Agentic Analytics

Monorepo containing four Python sub-projects for autonomous log analytics, anomaly
detection, root cause analysis, and multi-agent observability using LangGraph, CrewAI,
LangChain, FAISS, MCP, and Gradio.

## Repository Layout

```
lognexus-agentic-analytics/
├── src/
│   ├── observability/   # Multi-agent observability pipeline (EventBus + Pushover)
│   ├── anomaly-eval/    # HDFS/BGL log anomaly detection + ROC evaluation
│   ├── mcp-pipeline/    # Agentic observability + MCP server + Claude AI agent UI
│   └── rca-engine/      # LangGraph + CrewAI RCA pipeline with Gradio dashboard
├── build/               # Per-package virtual environments (created by build.sh)
├── install/             # Shared environment setup
├── deploy/              # Service launch scripts and runtime logs
└── test/                # Unit tests
```

## Getting Started

Install all dependencies into a shared `.venv`:

```bash
bash install/install.sh
source .venv/bin/activate
```

Or build isolated per-package environments under `build/`:

```bash
bash build/build.sh
```

Start all services (uses tmux if available, falls back to background processes):

```bash
bash deploy/deploy.sh start
bash deploy/deploy.sh stop
bash deploy/deploy.sh status
bash deploy/deploy.sh logs
```

Run the unit tests:

```bash
python -m pytest test/ -v
```

## Sub-projects

### observability

Multi-agent observability system with three parallel agents (Monitor, Correlation, RCA)
communicating over a shared EventBus. Integrates Loki log fetching, FAISS-backed RAG,
LLM-based RCA, and Pushover push notifications. Gradio control dashboard on port 7861.

```bash
cd src/observability
pip install -r requirements.txt
export OPENAI_API_KEY=...
python3 main.py
```

Dashboard: `http://localhost:7861/`

---

### anomaly-eval

Offline evaluation framework comparing TF-IDF + Logistic Regression against a
rule-based detector on HDFS and BGL log datasets. Produces precision/recall/F1
metrics and a combined ROC curve PDF.

```bash
cd src/anomaly-eval
pip install -r requirements.txt
# Place HDFS.log and BGL.log under data/
python3 main.py
```

---

### mcp-pipeline

Extends the agentic observability stack with a FastMCP server exposing 7 tools
(anomaly detection, incident correlation, RCA, knowledge base search, metrics,
live logs, notification). Includes a Gradio-based Claude agent UI on port 9861.

```bash
cd src/mcp-pipeline
pip install -r requirements.txt
pip install -r requirements_mcp.txt
export OPENAI_API_KEY=...
export ANTHROPIC_API_KEY=...

python3 main.py

# MCP + Claude AI agent UI (separate terminal)
python3 mcp/mcp_gradio_demo.py
```

MCP Agent UI: `http://localhost:9861/`

---

### rca-engine

End-to-end AIOps pipeline using LangGraph StateGraph with a conditional retry loop
driving CrewAI LLM agents for root cause analysis. Includes MCP tool stubs and a
FAISS RAG store. Live Gradio dashboard with Graphviz workflow visualiser on port 8860.

```bash
cd src/rca-engine
pip install -r requirements.txt
export OPENAI_API_KEY=...
python3 app.py
```

Dashboard: `http://localhost:8860/`

---

## Environment Variables

| Variable            | Used by                               |
|---------------------|---------------------------------------|
| `OPENAI_API_KEY`    | All sub-projects using LLM / RAG      |
| `ANTHROPIC_API_KEY` | mcp-pipeline (Claude agent UI)        |
| `PUSHOVER_TOKEN`    | observability, mcp-pipeline           |
| `PUSHOVER_USER`     | observability, mcp-pipeline           |
| `LOKI_URL`          | observability, mcp-pipeline           |
| `USE_LLM`           | mcp-pipeline (enables LLM-based RCA)  |

## License

Internal use only — VIAVI Solutions.
