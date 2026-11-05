from crewai import Agent

monitor_agent = Agent(
    role="Monitoring Agent",
    goal="Detect anomalies in logs using threshold",
    backstory="Expert in log monitoring and anomaly detection in distributed systems",
    verbose=False,
)

correlation_agent = Agent(
    role="Correlation Agent",
    goal="Group related logs into incidents",
    backstory="Expert in correlating events across microservices and identifying incident patterns",
    verbose=False,
)

rca_agent = Agent(
    role="RCA Agent",
    goal="Perform root cause analysis using logs and context",
    backstory="Expert in AIOps, diagnosing failures, and identifying root causes in cloud systems",
    verbose=False,
)
