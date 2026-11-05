def monitoring_agent(state):
    state.setdefault("steps", [])
    state["steps"].append("Monitoring Agent running")
    state["anomaly_score"] = 0.82
    state["threshold"] = 0.75
    return state
