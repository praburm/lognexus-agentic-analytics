import gradio as gr
import time
import random
import matplotlib.pyplot as plt

from graph.workflow import build_graph
from rag.vector_store import build_vector_store
from graphviz import Digraph

logs = ["UserService request", "DB timeout", "Failure"]
docs = ["DB overload causes timeout", "Service dependency failure"]

db    = build_vector_store(docs)
graph = build_graph()

log_text = ""


def generate_workflow_diagram(active_node=None, confidence=0.5):
    dot = Digraph(format="png")
    dot.attr(rankdir="LR", bgcolor="black", size="12,3")

    def style(n):
        if n == active_node:
            return {"style": "filled,bold", "color": "#00FFAA", "penwidth": "4"}
        return {"style": "filled", "color": "#444"}

    dot.node("A", "Monitoring",  **style("A"))
    dot.node("B", "Correlation", **style("B"))
    dot.node("C", "RCA",         **style("C"))
    dot.node("M", "MCP Tools",   style="filled", color="#888")
    dot.node("D", "Decision",    **style("D"))
    dot.node("E", "END",         **style("E"))

    dot.edge("A", "B", color="white")
    dot.edge("B", "C", color="white")
    dot.edge("C", "M", color="yellow")
    dot.edge("M", "D", color="yellow")
    dot.edge("D", "E", color="lime")
    dot.edge("D", "C", label="Retry", color="orange")

    fname = f"wf_{active_node}_{int(confidence * 100)}"
    dot.render(fname, cleanup=True)
    return fname + ".png"


def plot_all_charts(db_data, api_data, cache_data, conf_data):
    fig, axs = plt.subplots(2, 2, figsize=(10, 6))
    fig.patch.set_facecolor("#0b1220")

    datasets = [
        (db_data,    "DB Anomaly",  0.7),
        (api_data,   "API Latency", 0.7),
        (cache_data, "Cache",       0.7),
        (conf_data,  "Confidence",  0.75),
    ]

    for ax, (data, title, threshold) in zip(axs.flatten(), datasets):
        ax.set_facecolor("#0b1220")
        ax.plot(data, marker="o")
        for i, val in enumerate(data):
            if val > threshold:
                ax.scatter(i, val, s=80)
        ax.axhline(y=threshold)
        ax.set_title(title, color="white", fontsize=10)
        ax.tick_params(colors="white")
        ax.grid(True, color="#333")
        for spine in ax.spines.values():
            spine.set_color("white")

    plt.tight_layout()
    return fig


def run_demo():
    global log_text
    log_text = ""

    confidence = 0.5
    retry      = 0
    db_data    = []
    api_data   = []
    cache_data = []
    conf_hist  = []

    try:
        for i in range(3):
            base      = 0.2 + i * 0.15
            db_val    = base + random.uniform(0.05, 0.2)
            api_val   = base + random.uniform(0.02, 0.15)
            cache_val = base + random.uniform(0.01, 0.1)

            if i == 2:
                db_val += 0.3

            db_data.append(round(db_val, 2))
            api_data.append(round(api_val, 2))
            cache_data.append(round(cache_val, 2))
            confidence += 0.02
            conf_hist.append(confidence)

            log_text += f"\nMonitoring step {i}"
            yield update_ui("A", confidence, retry, db_data, api_data, cache_data, conf_hist, "RUNNING")
            time.sleep(1)

        log_text += "\nCorrelation phase"
        yield update_ui("B", confidence, retry, db_data, api_data, cache_data, conf_hist, "RUNNING")
        time.sleep(1)

        log_text += "\n[MCP] Fetching external metrics..."
        yield update_ui("M", confidence, retry, db_data, api_data, cache_data, conf_hist, "MCP FETCH")
        time.sleep(1)

        while confidence < 0.75:
            retry     += 1
            confidence += 0.1
            conf_hist.append(confidence)
            log_text += f"\nRCA attempt {retry}"
            yield update_ui("C", confidence, retry, db_data, api_data, cache_data, conf_hist, "RETRY")
            time.sleep(1)

        result     = graph.invoke({"logs": logs, "db": db, "steps": []})
        confidence = result.get("confidence", confidence)

        root_cause = result.get("root_cause", "No RCA available")
        reasoning  = result.get("reasoning", "")
        actions    = result.get("actions", [])
        actions_md = "\n".join([f"- {a}" for a in actions])

        rca_text = f"### Root Cause\n**{root_cause}**\n\n---\n\n### Reasoning\n{reasoning}\n\n---\n\n### Recommended Actions\n{actions_md}"

        yield update_ui("E", confidence, retry, db_data, api_data, cache_data, conf_hist, "SUCCESS", rca_text)

    except Exception as e:
        yield None, str(e), "Error", "Error", None, "", "", ""


def update_ui(node, conf, retry, db_data, api_data, cache_data, conf_hist, status, rca=""):
    graph_img = generate_workflow_diagram(node, conf)
    charts    = plot_all_charts(db_data, api_data, cache_data, conf_hist)
    color     = "red" if max(db_data) > 0.75 else "orange" if "RETRY" in status else "green"
    alert     = f"<div style='background:{color};padding:10px;color:white'>{status}</div>"
    services  = f"DB Load: {db_data[-1]:.2f} | API Latency: {api_data[-1]:.2f} | Cache Hit: {cache_data[-1]:.2f}"

    return (graph_img, log_text, rca, f"{conf:.2f}", charts, alert, services, str(retry))


with gr.Blocks() as demo:
    gr.Markdown("# Autonomous Log Analytics AIOps Dashboard")

    run_btn = gr.Button("Run Analysis")
    alert   = gr.HTML()

    with gr.Row():
        confidence = gr.Textbox(label="Confidence Score")
        retry_box  = gr.Textbox(label="Retry Count")

    services = gr.Textbox(label="Services")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Multi-Agent Workflow (LangGraph + CrewAI + MCP)")
            graph_img = gr.Image(height=250, show_label=False)
            flow      = gr.Textbox(lines=6, show_label=False)

        with gr.Column(scale=1.3):
            charts = gr.Plot(label="System Metrics Dashboard")

    with gr.Accordion("Root Cause Analysis"):
        rca = gr.Markdown()

    run_btn.click(
        run_demo,
        outputs=[graph_img, flow, rca, confidence, charts, alert, services, retry_box],
    )

demo.launch(server_port=8860)
