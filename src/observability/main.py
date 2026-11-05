import threading
from utils.event_bus import EventBus
from agents.agentic_monitor_agent import AgenticMonitorAgent
from agents.agentic_correlation_agent import AgenticCorrelationAgent
from agents.agentic_rca_agent import AgenticRCAAgent


def main():
    # single shared bus — all agents communicate via queued events
    event_bus = EventBus()

    monitor = AgenticMonitorAgent(event_bus)
    correlator = AgenticCorrelationAgent(event_bus)
    rca = AgenticRCAAgent(event_bus)

    threads = [
        threading.Thread(target=monitor.run, daemon=True),
        threading.Thread(target=correlator.run, daemon=True),
        threading.Thread(target=rca.run, daemon=True),
    ]

    for t in threads:
        t.start()

    for t in threads:
        t.join()


if __name__ == "__main__":
    main()
