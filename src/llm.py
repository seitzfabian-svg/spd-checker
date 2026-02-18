import os
import json
from openai import OpenAI

def decide_with_llm(user_inputs, evidence_chunks):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to Streamlit Secrets.")

    model = os.getenv("OPENAI_MODEL", "gpt-5.2")
    client = OpenAI(api_key=api_key)

    # Striktes Output-Schema
    out_schema = {
        "Genehmigung": "Ja | Nein | Manuelle Prüfung",
        "Genehmigungsbetrag": 0.0,
        "Empfehlung": "string"
    }

    system = """
Du bist ein strenger Regelprüfer für eine SPD-Prozessbeschreibung im Minimalformat.
WICHTIG:
- Du darfst NUR auf Basis der übergebenen EVIDENZ-CHUNKS (aus dem SPD-Dokument) entscheiden.
- KEIN externes Wissen. KEINE Annahmen. KEINE Halluzinationen.
- Die SPD-Prozessbeschreibung enthält nur [INPUTS], [DWH], [RULES], [DEFAULT].
- Wenn eine Regel nicht eindeutig anwendbar ist oder Informationen fehlen -> Genehmigung="Manuelle Prüfung".
- Output MUSS gültiges JSON sein und exakt die Felder: Genehmigung, Genehmigungsbetrag, Empfehlung.
- Genehmigungsbetrag nur >0 wenn Genehmigung="Ja", sonst 0.
"""

    prompt = f"""
INPUTS (User + DWH):
{json.dumps(user_inputs, ensure_ascii=False, indent=2)}

EVIDENZ-CHUNKS (einzige Quelle, daraus musst du Regeln ableiten und anwenden):
{json.dumps(evidence_chunks, ensure_ascii=False, indent=2)}

AUFGABE:
1) Extrahiere aus den EVIDENZ-CHUNKS die relevanten RULES und DEFAULT.
2) Wende Regeln strikt auf die Inputs an.
3) Gib JSON-Output zurück (nur diese Struktur):
{json.dumps(out_schema, ensure_ascii=False, indent=2)}

REGELN FÜR ENTSCHEIDUNG:
- "Ja": wenn eine Regel eine Genehmigung explizit erlaubt und der genehmigte Betrag ableitbar ist.
- "Nein": wenn eine Regel explizit ablehnt.
- sonst "Manuelle Prüfung": und Empfehlung kurz nennen (z.B. "fehlende Regel/fehlende Daten").

Gib NUR JSON aus, keine Erklärtexte.
"""

    resp = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        max_output_tokens=350
    )

    out = getattr(resp, "output_text", None)
    if not out:
        # hard fallback
        return ({
            "Genehmigung": "Manuelle Prüfung",
            "Genehmigungsbetrag": 0.0,
            "Empfehlung": "LLM lieferte kein Output."
        }, evidence_chunks)

    try:
        data = json.loads(out)
        # Minimal normalize keys (falls LLM casing versaubeutelt)
        data = {
            "Genehmigung": data.get("Genehmigung", "Manuelle Prüfung"),
            "Genehmigungsbetrag": float(data.get("Genehmigungsbetrag", 0.0) or 0.0),
            "Empfehlung": data.get("Empfehlung", "") or ""
        }
        return (data, evidence_chunks)
    except Exception:
        return ({
            "Genehmigung": "Manuelle Prüfung",
            "Genehmigungsbetrag": 0.0,
            "Empfehlung": "Output war kein gültiges JSON. Bitte erneut prüfen."
        }, evidence_chunks)
