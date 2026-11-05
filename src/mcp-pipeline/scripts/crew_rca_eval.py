from crewai import Agent, Task, Crew


def validate_rca(logs: str, rca_output: dict):
    rca_agent = Agent(
        role="RCA Agent",
        goal="Determine the most likely root cause from logs",
        backstory="Expert SRE with deep system knowledge",
    )

    reviewer_agent = Agent(
        role="SRE Reviewer",
        goal="Validate RCA accuracy and suggest improvements",
        backstory="Senior production reliability engineer",
    )

    task = Task(
        description=f"Logs:\n{logs}\n\nRCA Output:\n{rca_output}\n\nValidate correctness, confidence, and actions.",
        agent=rca_agent,
    )

    crew = Crew(agents=[rca_agent, reviewer_agent], tasks=[task])
    return crew.kickoff()


if __name__ == "__main__":
    logs = "ERROR: application timeout at service A"
    rca = {"root_cause": "Application latency spike"}
    print(validate_rca(logs, rca))
