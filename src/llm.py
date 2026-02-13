import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def decide_with_llm(user_inputs, evidence):

    prompt = f"""
Du darfst ausschließlich auf Basis folgender Dokumentstellen entscheiden:

{evidence}

User Inputs:
{user_inputs}

Regeln:
- Keine Annahmen
- Keine Halluzination
- Wenn unklar → "Manuelle Prüfung"

Gib JSON zurück:
{{
  "decision": "...",
  "rationale": "...",
  "evidence": [...]
}}
"""

    response = client.responses.create(
        model="gpt-5.2",
        input=prompt
    )

    return eval(response.output_text)
