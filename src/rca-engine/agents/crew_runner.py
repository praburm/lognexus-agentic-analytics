import json
from crewai import Crew, LLM
from agents.crew_agents import rca_agent
from agents.tasks import rca_task
from mcp.tools import fetch_metrics, fetch_logs


def run_crew(state):
    state.setdefault("steps", [])

    logs = state.get("logs", [])
    metrics = fetch_metrics()
    extra_logs = fetch_logs()

    if isinstance(logs, str):
        logs = [logs]
    elif isinstance(logs, dict):
        logs = [str(logs)]

    enriched_logs = logs + extra_logs

    llm = LLM(model="gpt-4o-mini", temperature=0.2)
    rca_agent.llm = llm

    crew = Crew(agents=[rca_agent], tasks=[rca_task], verbose=False)
    result = crew.kickoff(inputs={"logs": "\n".join(enriched_logs), "metrics": metrics})

    raw = str(result)
    try:
        parsed = json.loads(raw)
    except Exception:
        parsed = {"root_cause": raw, "reasoning": "", "confidence": 0.5, "actions": []}

    state["root_cause"] = parsed.get("root_cause", "Unknown")
    state["reasoning"]  = parsed.get("reasoning", "")
    state["confidence"] = parsed.get("confidence", 0.5)
    state["actions"]    = parsed.get("actions", [])
    state["steps"].append("RCA completed")

    return state
