import gradio as gr
import json
import glob
import os
import pandas as pd
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INCIDENT_DIR = os.path.join(BASE_DIR, "..", "data", "incidents")
EXPORT_DIR = os.path.join(BASE_DIR, "..", "data", "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)


def load_latest_incident():
    if not os.path.isdir(INCIDENT_DIR):
        return None, None, "Incident directory not found"

    files = sorted(glob.glob(os.path.join(INCIDENT_DIR, "INC-*.json")))
    if not files:
        return None, None, "No incidents found"

    with open(files[-1]) as f:
        rca = json.load(f)

    metrics = rca.get("metrics", {})
    metrics_df = (
        pd.DataFrame(metrics.items(), columns=["Metric", "Value"])
        if metrics
        else pd.DataFrame([["N/A", "No metrics present"]], columns=["Metric", "Value"])
    )

    rule_rows = [
        [rc.get("cause"), rc.get("confidence"), rc.get("action")]
        for rc in rca.get("rule_based_rca", [])
    ]
    rca_df = pd.DataFrame(rule_rows, columns=["Rule Cause", "Confidence", "Action"])

    llm = rca.get("llm_rca", {}).get("analysis", {})
    llm_text = (
        f"Incident ID: {rca.get('incident_id')}\n"
        f"Categories: {', '.join(rca.get('categories', []))}\n"
        f"Analyzed At: {datetime.fromtimestamp(rca.get('analyzed_at', 0))}\n\n"
        f"Root Cause: {llm.get('root_cause')}\n"
        f"Confidence: {llm.get('confidence')}\n\n"
        "Recommended Actions:\n"
        + "\n".join(f"- {a}" for a in llm.get("recommended_actions", []))
    )

    return metrics_df, rca_df, llm_text


def export_latest_incident():
    files = sorted(glob.glob(os.path.join(INCIDENT_DIR, "INC-*.json")))
    if not files:
        return "No incidents to export"

    with open(files[-1]) as f:
        rca = json.load(f)

    incident_id = rca.get("incident_id", "unknown")

    metrics_df = pd.DataFrame(rca.get("metrics", {}).items(), columns=["Metric", "Value"])
    metrics_csv = os.path.join(EXPORT_DIR, f"{incident_id}_metrics.csv")
    metrics_df.to_csv(metrics_csv, index=False)

    rca_df = pd.DataFrame(
        [[r["cause"], r["confidence"], r["action"]] for r in rca.get("rule_based_rca", [])],
        columns=["Cause", "Confidence", "Action"],
    )
    rca_csv = os.path.join(EXPORT_DIR, f"{incident_id}_rca.csv")
    rca_df.to_csv(rca_csv, index=False)

    html_path = os.path.join(EXPORT_DIR, f"{incident_id}.html")
    html = f"""<html>
<head>
    <title>{incident_id} - RCA Report</title>
    <style>
        body {{ font-family: Arial; margin: 40px; }}
        h2 {{ color: #2c3e50; }}
        table {{ border-collapse: collapse; width: 80%; }}
        th, td {{ border: 1px solid #ccc; padding: 8px; }}
        th {{ background-color: #f4f4f4; }}
    </style>
</head>
<body>
    <h2>Incident Report: {incident_id}</h2>
    <h3>Categories</h3>
    <p>{', '.join(rca.get('categories', []))}</p>
    <h3>Semantic Metrics</h3>
    {metrics_df.to_html(index=False)}
    <h3>Rule-based RCA</h3>
    {rca_df.to_html(index=False)}
    <h3>LLM Analysis</h3>
    <pre>{json.dumps(rca.get("llm_rca", {}), indent=2)}</pre>
</body>
</html>"""

    with open(html_path, "w") as f:
        f.write(html)

    return f"Exported files:\n- {metrics_csv}\n- {rca_csv}\n- {html_path}"


with gr.Blocks(title="Agentic AI Log Analyzer") as demo:
    gr.Markdown("## Semantic Metrics")
    metrics_table = gr.Dataframe(interactive=False)

    gr.Markdown("## RCA Summary")
    rca_table = gr.Dataframe(interactive=False)

    gr.Markdown("## LLM Root Cause Explanation")
    llm_box = gr.Textbox(lines=12)

    load_btn = gr.Button("Load Latest Incident")
    export_btn = gr.Button("Export to File")
    status_box = gr.Textbox(label="Export Status")

    load_btn.click(fn=load_latest_incident, outputs=[metrics_table, rca_table, llm_box])
    export_btn.click(fn=export_latest_incident, outputs=status_box)

demo.launch(server_name="0.0.0.0", server_port=7860)
