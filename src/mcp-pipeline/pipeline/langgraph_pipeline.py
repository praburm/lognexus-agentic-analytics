from langgraph.graph import StateGraph
from typing import Dict, Any

from agents.agentic_monitor_agent import run_monitor_agent
from agents.agentic_correlation_agent import run_correlation_agent
from agents.agentic_rca_agent import run_rca_agent
from utils.semantic_enricher import enrich_events


class LogState(dict):
    pass


def monitor_node(state: LogState) -> LogState:
    events, metrics = run_monitor_agent(state["logs"])
    state["events"] = events
    state["metrics"] = metrics
    return state


def semantic_node(state: LogState) -> LogState:
    state["events"] = enrich_events(state["events"])
    return state


def correlation_node(state: LogState) -> LogState:
    state["correlations"] = run_correlation_agent(state["events"])
    return state


def rca_node(state: LogState) -> LogState:
    state["rca"] = run_rca_agent(state["correlations"])
    return state


def build_workflow():
    graph = StateGraph(LogState)

    graph.add_node("monitor", monitor_node)
    graph.add_node("semantic", semantic_node)
    graph.add_node("correlate", correlation_node)
    graph.add_node("rca", rca_node)

    graph.add_edge("monitor", "semantic")
    graph.add_edge("semantic", "correlate")
    graph.add_edge("correlate", "rca")

    graph.set_entry_point("monitor")

    return graph.compile()


workflow = build_workflow()


def run_pipeline(log_text: str) -> Dict[str, Any]:
    return workflow.invoke({"logs": log_text})
