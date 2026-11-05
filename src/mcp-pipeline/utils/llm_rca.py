import os
import json
import re
from openai import OpenAI
from rag.rag_store import retrieve_context

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def json_safe(obj):
    if isinstance(obj, set):
        return list(obj)
    return obj


def llm_rca(incident):
    categories = list(incident.get("categories", []))
    alert_count = len(incident.get("alerts", []))

    query = f"Incident categories: {categories}\nAlert count: {alert_count}\nSimilar past incidents, known root causes and fixes"
    rag_context = retrieve_context(query)

    prompt = f"""
You are a Site Reliability Engineer performing Root Cause Analysis.

Incident:
{json.dumps(incident, indent=2, default=json_safe)}

Historical incidents, runbooks, and fixes:
{rag_context}

Respond strictly in JSON with:
- root_cause
- confidence (0 to 1)
- recommended_actions
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )

    raw = response.choices[0].message.content.strip()
    clean = re.sub(r"```json|```", "", raw).strip()

    try:
        analysis = json.loads(clean)
    except Exception:
        analysis = {"raw_response": clean, "parse_error": True}

    return {"rag_used": bool(rag_context), "analysis": analysis}
