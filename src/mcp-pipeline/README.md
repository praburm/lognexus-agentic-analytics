# LogNexus Agentic MCP Demo

Extends the agentic observability platform with a Model Context Protocol (MCP) layer.
Claude claude-sonnet-4-6 orchestrates the full log analytics pipeline — anomaly detection,
semantic enrichment, incident correlation, and RCA — via MCP-style tool use.

## Architecture

```
User Query
    │
    ▼
Claude claude-sonnet-4-6  (Anthropic SDK)
    │  tool_use / tool_result
    ▼
TOOL_REGISTRY  (mcp/mcp_server.py)
    ├── fetch_sample_logs          K8s sample logs (4 scenarios)
    ├── parse_and_detect_anomalies ErrorSpike / TimeoutSpike / RarePattern
    ├── semantic_analysis          novelty · anomaly · pattern IDs
    ├── correlate_alerts           incident creation + severity
    ├── root_cause_analysis        rule-based RCA + optional LLM enrichment
    ├── list_incidents             historical incident records
    └── search_knowledge_base      FAISS RAG / built-in runbooks
```

## Project Structure

```
lognexus_agentic-mcp-demo/
├── agents/          # Monitor, Correlation, RCA agents
├── pipeline/        # LangGraph pipeline
├── rag/             # FAISS RAG store
├── dashboard/       # Gradio control dashboard
├── mcp/
│   ├── mcp_server.py        # MCP tool definitions + TOOL_REGISTRY
│   └── mcp_gradio_demo.py   # Claude + MCP Gradio UI (port 9861)
├── data/
│   ├── incidents/
│   ├── exports/
│   └── logs/
├── scripts/
├── utils/
├── main.py
├── requirements.txt
└── requirements_mcp.txt
```

## Installation

```bash
cd src/mcp-pipeline
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements_mcp.txt
```

## Environment Variables

| Variable             | Required | Description                            |
|----------------------|----------|----------------------------------------|
| `ANTHROPIC_API_KEY`  | Yes      | Claude API key for MCP demo            |
| `USE_LLM`            | Optional | Enable LLM-powered RCA (`true`/`false`)|
| `OPENAI_API_KEY`     | Optional | OpenAI key for LLM RCA + embeddings    |
| `PUSHOVER_USER_KEY`  | Optional | Pushover notifications                 |
| `PUSHOVER_APP_TOKEN` | Optional | Pushover notifications                 |

## Execution

### MCP Demo (Claude + tool use UI)

```bash
source venv/bin/activate
export ANTHROPIC_API_KEY=...
python3 mcp/mcp_gradio_demo.py
```

Open: `http://localhost:9861/`

### Control Dashboard (agentic pipeline)

```bash
source venv/bin/activate
export USE_LLM=true
export OPENAI_API_KEY=...
python3 dashboard/agentic_control_dashboard.py
```

Open: `http://localhost:7861/`

### Headless agent runner

```bash
python3 main.py
```

### MCP Server (standalone, requires Python 3.10+ and mcp[cli])

```bash
python3 mcp/mcp_server.py
```

## License

Internal use only — VIAVI Solutions.
