# LogNexus AIOps RCA Demo

Autonomous log analytics platform combining LangGraph, CrewAI, and MCP tools
into a multi-agent pipeline with a live Gradio dashboard.

## Architecture

```
Gradio Dashboard (app.py — port 8860)
        │
        ▼
LangGraph StateGraph
        │
        ├── Monitoring Agent      → detects anomaly score vs threshold
        │         │ (conditional)
        ├── Correlation Agent     → groups logs into incident
        │         │
        ├── MCP Tools             → fetches external metrics + logs
        │         │
        └── RCA Agent (CrewAI)    → LLM-powered root cause analysis
                  │ (conditional retry until confidence >= 0.75)
                  ▼
              RCA Result (root_cause, reasoning, confidence, actions)
```

## Project Structure

```
lognexus_aiops-rca-demo/
├── agents/
│   ├── monitoring.py      # Anomaly score detection
│   ├── correlation.py     # Log grouping into incidents
│   ├── crew_agents.py     # CrewAI agent definitions
│   ├── crew_runner.py     # LLM-powered RCA via CrewAI
│   └── tasks.py           # CrewAI task definition
├── graph/
│   └── workflow.py        # LangGraph StateGraph with conditional retry loop
├── mcp/
│   └── tools.py           # MCP-style tool stubs (metrics + logs)
├── rag/
│   ├── vector_store.py    # FAISS vector store builder
│   └── retriever.py       # Similarity search retrieval
├── app.py                 # Gradio dashboard + workflow visualiser
└── requirements.txt
```

## Installation

```bash
cd src/rca-engine
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

## Environment Variables

| Variable         | Required | Description                     |
|------------------|----------|---------------------------------|
| `OPENAI_API_KEY` | Yes      | OpenAI key for CrewAI LLM + RAG |

```bash
export OPENAI_API_KEY=...
```

## Execution

```bash
source venv/bin/activate
export OPENAI_API_KEY=...
python3 app.py
```

Open: `http://localhost:8860/`

Click **Run Analysis** to start the full pipeline.

## Agent Flow

| Step | Agent | Action |
|---|---|---|
| 1 | Monitoring Agent | Computes anomaly score — if >= threshold, continues |
| 2 | Correlation Agent | Groups logs into an incident record |
| 3 | MCP Tools | Fetches live metrics and additional log context |
| 4 | RCA Agent (CrewAI) | LLM analysis — retries if confidence < 0.75 |
| 5 | Dashboard | Renders root cause, reasoning, and recommended actions |

## License

Internal use only — VIAVI Solutions.
