def correlation_agent(state):
    state.setdefault("steps", [])
    state["steps"].append("Correlation Agent grouping logs")
    logs = state.get("logs", [])
    state["incident"] = {"count": len(logs)}
    return state
