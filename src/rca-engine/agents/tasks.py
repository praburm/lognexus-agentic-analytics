from crewai import Task
from agents.crew_agents import rca_agent

rca_task = Task(
    description="""
You are an AIOps expert.

Analyze the following logs and metrics:

Logs:
{logs}

Metrics:
{metrics}

Provide output in JSON format:
{{
  "root_cause": "...",
  "reasoning": "...",
  "confidence": 0.0-1.0,
  "actions": ["...", "..."]
}}
""",
    expected_output="Structured RCA with reasoning, confidence, and actions",
    agent=rca_agent,
)
