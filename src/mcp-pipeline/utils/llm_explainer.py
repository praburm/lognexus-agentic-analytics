from openai import OpenAI

client = OpenAI()

def explain(alert, related_logs):
    prompt = f"""
You are an SRE assistant.

Alert:
{alert}

Relevant logs:
{related_logs}

Tasks:
1. Identify root cause
2. Affected service
3. Severity
4. Suggested remediation steps
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return response.choices[0].message.content
