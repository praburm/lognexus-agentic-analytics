import json
import os
import sys
import textwrap

import gradio as gr

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from mcp.mcp_server import TOOL_REGISTRY

SYSTEM_PROMPT = textwrap.dedent("""
    You are a senior Site Reliability Engineer (SRE) with expertise in
    Kubernetes log analysis, incident management, and root cause analysis.

    You have access to a production-grade log analytics pipeline as MCP tools:
    • fetch_sample_logs           — Retrieve sample K8s logs for a scenario
    • parse_and_detect_anomalies  — Detect ErrorSpike / TimeoutSpike / RareLogPattern
    • semantic_analysis           — Compute novelty, anomaly scores, and pattern IDs
    • correlate_alerts            — Group alerts into a categorized incident
    • root_cause_analysis         — Rule-based RCA with remediation actions
    • list_incidents              — Browse historical incident records
    • search_knowledge_base       — Find similar past incidents and runbooks

    When analyzing logs, follow this pipeline:
    1. Fetch or accept the log data
    2. Detect anomalies (parse_and_detect_anomalies)
    3. Enrich semantics (semantic_analysis)
    4. Correlate into an incident (correlate_alerts)
    5. Perform root cause analysis (root_cause_analysis)
    6. Optionally search the knowledge base for historical context
    7. Provide a concise, actionable summary with clear next steps

    Be specific: cite tool output values (error counts, severity, services).
    Format your final answer in clear Markdown with headers and bullet points.
""").strip()

QUICK_ACTIONS = [
    ("Error Spike",
     "Fetch the 'error_spike' scenario logs and run the full pipeline: "
     "detect anomalies, enrich semantics, correlate into an incident, and perform "
     "root cause analysis. Summarize findings with actionable remediation steps."),
    ("Timeout Cascade",
     "Fetch the 'timeout_spike' logs, investigate the timeout cascade, identify "
     "affected services, correlate the incident, search the knowledge base for "
     "similar past issues, and recommend fixes."),
    ("Multi-Service Incident",
     "Fetch the 'complex_incident' scenario and analyze the multi-service cascading "
     "failure. Run the full pipeline and explain the chain of failures with severity "
     "assessment and a step-by-step recovery plan."),
    ("List Incidents",
     "List the 5 most recent persisted incidents and give a brief summary of each "
     "one's category, severity, and top root cause."),
    ("Search KB",
     "Search the knowledge base for 'database connection pool timeout' and "
     "'cascading auth failure'. Summarize the most relevant runbooks."),
    ("Healthy Baseline",
     "Fetch the 'normal' scenario logs, run anomaly detection and semantic analysis, "
     "and confirm the system is healthy with baseline metrics."),
]

_TOOL_COLOUR = {
    "fetch_sample_logs":          "#2d8cf0",
    "parse_and_detect_anomalies": "#ff6b35",
    "semantic_analysis":          "#9c27b0",
    "correlate_alerts":           "#e91e63",
    "root_cause_analysis":        "#f44336",
    "list_incidents":             "#4caf50",
    "search_knowledge_base":      "#009688",
}
_TOOL_ICON = {
    "fetch_sample_logs":          "fetch",
    "parse_and_detect_anomalies": "detect",
    "semantic_analysis":          "semantic",
    "correlate_alerts":           "correlate",
    "root_cause_analysis":        "rca",
    "list_incidents":             "list",
    "search_knowledge_base":      "search",
}


def _tool_card(name, inputs, result, status):
    colour  = _TOOL_COLOUR.get(name, "#607d8b")
    icon    = _TOOL_ICON.get(name, name)
    badge   = "Running" if status == "running" else "Done"
    b_bg    = "#ff9800" if status == "running" else "#4caf50"

    inp_str = json.dumps(inputs, indent=2)
    if len(inp_str) > 300:
        inp_str = inp_str[:300] + "\n  ..."

    result_block = ""
    if result is not None:
        preview = (result[:700] + "...") if len(result) > 700 else result
        preview = preview.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        result_block = (
            '<div style="margin-top:8px;background:#f8f9fa;border-radius:6px;'
            'padding:8px;max-height:200px;overflow-y:auto;">'
            '<span style="font-size:.73em;color:#666;font-weight:700;">RESULT</span>'
            f'<pre style="margin:4px 0 0;font-size:.77em;color:#333;'
            f'white-space:pre-wrap;word-break:break-word;">{preview}</pre></div>'
        )

    return (
        f'<div style="border-left:4px solid {colour};border-radius:8px;padding:12px 14px;'
        f'margin:6px 0;background:#fff;box-shadow:0 1px 4px rgba(0,0,0,.07);">'
        f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">'
        f'<span style="font-weight:700;color:{colour};font-size:.95em;">[{icon}] {name}</span>'
        f'<span style="margin-left:auto;background:{b_bg};color:#fff;border-radius:12px;'
        f'padding:2px 10px;font-size:.74em;font-weight:700;">{badge}</span></div>'
        f'<div style="background:#f0f7ff;border-radius:6px;padding:8px;">'
        f'<pre style="margin:4px 0 0;font-size:.77em;color:#333;'
        f'white-space:pre-wrap;word-break:break-word;">{inp_str}</pre></div>'
        f'{result_block}</div>'
    )


def _tool_panel(cards_html):
    if not cards_html:
        return ("<div style='color:#aaa;padding:30px;text-align:center;font-size:.9em;'>"
                "MCP tool calls will appear here as Claude works through your query.</div>")
    return (
        "<div style=\"font-family:'Segoe UI',system-ui,sans-serif;padding:4px;\">"
        f"{cards_html}</div>"
    )


def _claude_tools():
    return [{"name": name, "description": info["description"],
             "input_schema": info["input_schema"]}
            for name, info in TOOL_REGISTRY.items()]


def _call_tool(name, inputs):
    return TOOL_REGISTRY[name]["fn"](**inputs)


async def _agent_stream(user_query, history):
    try:
        import anthropic
    except ImportError:
        yield (history + [[user_query, "**Setup required:** `pip install anthropic`"]],
               _tool_panel(""), "Missing: anthropic")
        return

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        yield (history + [[user_query, "**Setup required:** `ANTHROPIC_API_KEY` not set."]],
               _tool_panel(""), "Missing: ANTHROPIC_API_KEY")
        return

    client       = anthropic.Anthropic(api_key=api_key)
    claude_tools = _claude_tools()
    messages     = [{"role": "user", "content": user_query}]
    cards        = []
    agent_text   = ""
    call_n       = 0

    yield (history + [[user_query, f"_Initialising MCP tool registry..._\n\n"
                       f"**Tools:** `{'`, `'.join(t['name'] for t in claude_tools)}`"]],
           _tool_panel(""), f"{len(claude_tools)} MCP tools ready")

    try:
        for _turn in range(14):
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=claude_tools,
                messages=messages,
            )

            for block in response.content:
                if hasattr(block, "text"):
                    agent_text += block.text

            if response.stop_reason == "end_turn":
                break

            if response.stop_reason == "tool_use":
                tool_results = []

                for block in response.content:
                    if block.type != "tool_use":
                        continue
                    call_n += 1
                    t_name, t_input = block.name, block.input

                    r_card = _tool_card(t_name, t_input, None, "running")
                    cards.append([t_name, t_input, block.id, r_card])
                    yield (history + [[user_query, agent_text or f"_Calling `{t_name}`..._"]],
                           _tool_panel("".join(c[3] for c in cards)),
                           f"[{call_n}] Calling {t_name}...")

                    try:
                        result_text = _call_tool(t_name, t_input)
                    except Exception as exc:
                        result_text = json.dumps({"error": str(exc)})

                    d_card = _tool_card(t_name, t_input, result_text, "done")
                    cards[-1] = [t_name, t_input, block.id, d_card]
                    yield (history + [[user_query, agent_text or f"_Processing `{t_name}` result..._"]],
                           _tool_panel("".join(c[3] for c in cards)),
                           f"[{call_n}] {t_name} complete")

                    tool_results.append({"type": "tool_result",
                                          "tool_use_id": block.id,
                                          "content": result_text})

                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user",      "content": tool_results})

    except Exception as exc:
        agent_text = agent_text or f"**Agent error:** {exc}"

    yield (history + [[user_query, agent_text or "_(no response generated)_"]],
           _tool_panel("".join(c[3] for c in cards)),
           f"Analysis complete — {call_n} tool call(s)")


_CSS = """
.gradio-container { max-width:1400px !important; }
#tool-panel-html  { background:#fafafa; border-radius:10px; padding:10px; min-height:200px; }
footer            { display:none !important; }
"""

with gr.Blocks(theme=gr.themes.Soft(primary_hue="blue", neutral_hue="slate"),
               css=_CSS, title="Log Analytics MCP Demo") as demo:

    gr.Markdown("## Log Analytics MCP Demo\nClaude claude-sonnet-4-6 orchestrates the log analytics pipeline via MCP-style tool use.")

    status_bar = gr.Textbox(value="Ready — select a Quick Action or type a question below.",
                            label="Agent Status", interactive=False)

    with gr.Row(equal_height=False):
        with gr.Column(scale=4):
            chatbot = gr.Chatbot(label="Conversation", height=440, bubble_full_width=False)
            with gr.Row():
                query_box  = gr.Textbox(
                    placeholder="e.g. 'Analyze error_spike logs and give me the root cause'",
                    label="Your question", lines=2, scale=6)
                submit_btn = gr.Button("Analyze", variant="primary", scale=1, min_width=110)

            clear_btn = gr.Button("Clear chat", size="sm", variant="secondary")

            gr.Markdown("#### Quick Actions")
            qa_buttons = []
            for row_start in (0, 3):
                with gr.Row():
                    for label, _query in QUICK_ACTIONS[row_start:row_start + 3]:
                        qa_buttons.append((gr.Button(label, size="sm", variant="secondary"), _query))

        with gr.Column(scale=5):
            gr.Markdown("#### Live MCP Tool Calls")
            tool_panel_html = gr.HTML(value=_tool_panel(""), elem_id="tool-panel-html")

    async def _on_submit(message, history):
        if not message.strip():
            yield history, _tool_panel(""), "Please enter a question."
            return
        async for step in _agent_stream(message, history):
            yield step

    submit_btn.click(fn=_on_submit, inputs=[query_box, chatbot],
                     outputs=[chatbot, tool_panel_html, status_bar], api_name=False
                     ).then(fn=lambda: gr.update(value=""), outputs=[query_box])

    query_box.submit(fn=_on_submit, inputs=[query_box, chatbot],
                     outputs=[chatbot, tool_panel_html, status_bar], api_name=False
                     ).then(fn=lambda: gr.update(value=""), outputs=[query_box])

    clear_btn.click(fn=lambda: ([], _tool_panel(""), "Chat cleared."),
                    outputs=[chatbot, tool_panel_html, status_bar], api_name=False)

    for btn, qa_query in qa_buttons:
        def _make_handler(q):
            async def _h(history):
                async for step in _agent_stream(q, history):
                    yield step
            return _h
        btn.click(fn=_make_handler(qa_query), inputs=[chatbot],
                  outputs=[chatbot, tool_panel_html, status_bar], api_name=False)


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY not set — queries will show an error until it is set.")
    print(f"Tools: {list(TOOL_REGISTRY.keys())}")
    print("UI: http://localhost:9861")
    demo.queue().launch(server_name="0.0.0.0", server_port=9861, share=False,
                        show_error=True, show_api=False)
