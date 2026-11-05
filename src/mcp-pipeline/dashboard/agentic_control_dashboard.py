import gradio as gr
import json
import glob
import os
import pandas as pd
import subprocess
import signal

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INCIDENT_DIR = os.path.join(BASE_DIR, "..", "data", "incidents")
LOG_DIR = os.path.join(BASE_DIR, "..", "data", "logs")
MAIN_SCRIPT = os.path.join(BASE_DIR, "..", "main.py")
ALERT_SCRIPT = os.path.join(BASE_DIR, "..", "scripts", "generate_alerts_v1.py")
K8S_NAMESPACE = "logan"

os.makedirs(LOG_DIR, exist_ok=True)

monitor_process = None
alert_process = None


def is_running(proc):
    return proc and proc.poll() is None


def get_microservices():
    try:
        result = subprocess.check_output(
            ["kubectl", "get", "pods", "-n", K8S_NAMESPACE],
            stderr=subprocess.STDOUT,
            text=True,
        )
        lines = result.strip().split("\n")
        rows = [line.split() for line in lines[1:]]
        return pd.DataFrame(rows, columns=["Pod", "Ready", "Status", "Restarts", "Age"])
    except Exception as e:
        return pd.DataFrame(
            [["N/A", "N/A", "kubectl error", "N/A", str(e)]],
            columns=["Pod", "Ready", "Status", "Restarts", "Age"],
        )


def get_agent_status():
    rows = [
        ["Monitor Agent", "Running" if is_running(monitor_process) else "Stopped"],
        ["Alert Agent", "Running" if is_running(alert_process) else "Stopped"],
        ["RCA Agent", "On-demand (LLM triggered)"],
    ]
    return pd.DataFrame(rows, columns=["Agent", "Status"])


def start_monitor():
    global monitor_process
    if is_running(monitor_process):
        return "Monitor Agent already running"
    log_file = open(os.path.join(LOG_DIR, "monitor.log"), "a")
    monitor_process = subprocess.Popen(
        ["python3", MAIN_SCRIPT],
        stdout=log_file,
        stderr=log_file,
        preexec_fn=os.setsid,
    )
    return "Monitor Agent started"


def start_alerts():
    global alert_process
    if is_running(alert_process):
        return "Alert Agent already running"
    log_file = open(os.path.join(LOG_DIR, "alerts.log"), "a")
    alert_process = subprocess.Popen(
        ["python3", ALERT_SCRIPT],
        stdout=log_file,
        stderr=log_file,
        preexec_fn=os.setsid,
    )
    return "Alert Agent started"


def stop_all():
    global monitor_process, alert_process
    msgs = []
    for name, proc in [("Monitor", monitor_process), ("Alert", alert_process)]:
        if is_running(proc):
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            msgs.append(f"{name} Agent stopped")
    monitor_process = None
    alert_process = None
    return "\n".join(msgs) if msgs else "No running agents"


def load_latest_incident():
    files = sorted(glob.glob(os.path.join(INCIDENT_DIR, "INC-*.json")))
    if not files:
        return None, None, "No incidents found"

    with open(files[-1]) as f:
        rca = json.load(f)

    metrics_df = pd.DataFrame(rca.get("metrics", {}).items(), columns=["Metric", "Value"])
    rules = [[r["cause"], r["confidence"], r["action"]] for r in rca.get("rule_based_rca", [])]
    rca_df = pd.DataFrame(rules, columns=["Cause", "Confidence", "Action"])

    llm = rca.get("llm_rca", {}).get("analysis", {})
    llm_text = (
        f"Incident ID: {rca.get('incident_id')}\n"
        f"Categories: {', '.join(rca.get('categories', []))}\n\n"
        f"Root Cause:\n{llm.get('root_cause')}\n\n"
        f"Confidence:\n{llm.get('confidence')}\n\n"
        "Recommended Actions:\n"
        + "\n".join(f"- {a}" for a in llm.get("recommended_actions", []))
    )

    return metrics_df, rca_df, llm_text.strip()


with gr.Blocks(title="Agentic AI Log Analyzer – Control Dashboard") as demo:
    gr.Markdown("## Agentic AI Log Analyzer – Control Dashboard")

    gr.Markdown("### Microservices Runtime (Kubernetes)")
    ms_table = gr.Dataframe(label="Pods in Namespace: logan", interactive=False)
    refresh_ms_btn = gr.Button("Refresh Microservices")
    refresh_ms_btn.click(get_microservices, outputs=ms_table)

    gr.Markdown("---")

    gr.Markdown("### Agent Status")
    agent_table = gr.Dataframe(interactive=False)
    refresh_agent_btn = gr.Button("Refresh Agent Status")
    refresh_agent_btn.click(get_agent_status, outputs=agent_table)

    gr.Markdown("---")

    gr.Markdown("### System Controls")
    with gr.Row():
        start_mon_btn = gr.Button("Start Monitor Agent")
        start_alert_btn = gr.Button("Start Alert Agent")
        stop_btn = gr.Button("Stop All Agents")

    status_box = gr.Textbox(label="System Status")
    start_mon_btn.click(start_monitor, outputs=status_box)
    start_alert_btn.click(start_alerts, outputs=status_box)
    stop_btn.click(stop_all, outputs=status_box)

    gr.Markdown("---")

    gr.Markdown("### Incident & Root Cause Analysis")
    with gr.Row():
        metrics_table = gr.Dataframe(label="Metrics", interactive=False)
        rca_table = gr.Dataframe(label="Rule-Based RCA", interactive=False)

    llm_box = gr.Textbox(label="LLM RCA Output", lines=12)
    load_btn = gr.Button("Load Latest Incident")
    load_btn.click(load_latest_incident, outputs=[metrics_table, rca_table, llm_box])

demo.launch(server_name="0.0.0.0", server_port=7861)
