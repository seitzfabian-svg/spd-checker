from dotenv import load_dotenv
load_dotenv()

import json
import streamlit as st

from src.parser import parse_document
from src.retrieval import build_retriever, retrieve_top_chunks
from src.llm import decide_with_llm
from src.render import render_decision_badge, render_evidence
from src.schema import DecisionOut

st.set_page_config(page_title="SPD Prozess-Checker", layout="wide")
st.title("SPD Prozess-Checker (Machbarkeitsprüfung)")
st.caption("Entscheidung ausschließlich aus der SPD-Prozessbeschreibung (Inputs/DWH/Rules). Sonst → Manuelle Prüfung.")

# ----------------------------
# Session State
# ----------------------------
if "doc_text" not in st.session_state:
    st.session_state.doc_text = None
if "retriever" not in st.session_state:
    st.session_state.retriever = None
if "chunks" not in st.session_state:
    st.session_state.chunks = None
if "result" not in st.session_state:
    st.session_state.result = None
if "evidence" not in st.session_state:
    st.session_state.evidence = None

col_left, col_right = st.columns([0.48, 0.52], gap="large")

with col_left:
    st.header("1) SPD-Prozessbeschreibung hochladen")
    uploaded = st.file_uploader("PDF oder TXT", type=["pdf", "txt"])

    if uploaded:
        try:
            text = parse_document(uploaded)
            retriever, chunks = build_retriever(text)

            st.session_state.doc_text = text
            st.session_state.retriever = retriever
            st.session_state.chunks = chunks

            st.success(f"Dokument verarbeitet. Zeichen: {len(text):,} | Chunks: {len(chunks)}")
            with st.expander("Vorschau (erste 2.000 Zeichen)"):
                st.text(text[:2000])

        except Exception as e:
            st.error(f"Parsing/Indexing fehlgeschlagen: {e}")

    st.divider()
    st.header("2) Inputvariablen")

    with st.form("input_form"):
        c1, c2 = st.columns(2)

        with c1:
            extOrdnungsbegriff = st.text_input("extOrdnungsbegriff", value="")
            extLeistungsangebot = st.text_input("extLeistungsangebot", value="")
            extRechnungsbetrag = st.number_input("extRechnungsbetrag", min_value=0.0, value=0.0, step=10.0)
            extRechnungsdatum = st.text_input("extRechnungsdatum (YYYY-MM-DD)", value="")
            extIBAN = st.text_input("extIBAN", value="")

        with c2:
            extBVEinmaligkeit = st.checkbox("extBVEinmaligkeit", value=False)
            sysQueueSelectorName = st.text_input("sysQueueSelectorName", value="")
            sysExternalId = st.text_input("sysExternalId", value="")
            extAbweichenderKontoinhaber = st.text_input("extAbweichenderKontoinhaber", value="")

        st.divider()
        st.subheader("DWH-Abfrage (Input)")

        dwh_prev_treatment = st.radio(
            "Gab es bereits eine vorherige Behandlung?",
            ["Ja", "Nein"],
            index=1,
            horizontal=True
        )
        dwh_total_refunded = st.number_input(
            "Wie viel wurde bisher erstattet (EUR)?",
            min_value=0.0,
            value=0.0,
            step=10.0
        )

        submit = st.form_submit_button("Prozess prüfen")

    if submit:
        if not st.session_state.retriever:
            st.error("Bitte zuerst eine SPD-Prozessbeschreibung hochladen.")
        else:
            inputs = {
                "extOrdnungsbegriff": extOrdnungsbegriff,
                "extLeistungsangebot": extLeistungsangebot,
                "extRechnungsbetrag": float(extRechnungsbetrag),
                "extRechnungsdatum": extRechnungsdatum,
                "extIBAN": extIBAN,
                "extBVEinmaligkeit": bool(extBVEinmaligkeit),
                "sysQueueSelectorName": sysQueueSelectorName,
                "sysExternalId": sysExternalId,
                "extAbweichenderKontoinhaber": extAbweichenderKontoinhaber,
                "dwh": {
                    "previous_treatment": True if dwh_prev_treatment == "Ja" else False,
                    "total_refunded_eur": float(dwh_total_refunded)
                }
            }

            evidence = retrieve_top_chunks(
                st.session_state.retriever,
                st.session_state.chunks,
                query=json.dumps(inputs, ensure_ascii=False),
                top_k=6
            )

            with st.spinner("Prüfung läuft (strikt dokumentbasiert) ..."):
                try:
                    out_json, debug = decide_with_llm(inputs, evidence)
                    # pydantic validate
                    result = DecisionOut.model_validate(out_json).model_dump()
                    st.session_state.result = result
                    st.session_state.evidence = debug
                except Exception as e:
                    st.error(f"LLM-Entscheidung fehlgeschlagen: {e}")

with col_right:
    st.header("3) Ergebnis")

    if st.session_state.result is None:
        st.info("Noch keine Prüfung ausgeführt.")
    else:
        render_decision_badge(st.session_state.result["Genehmigung"])

        st.subheader("Outputvariablen")
        st.write(f"**Genehmigung:** {st.session_state.result['Genehmigung']}")
        st.write(f"**Genehmigungsbetrag:** {st.session_state.result['Genehmigungsbetrag']}")
        st.write(f"**Empfehlung:** {st.session_state.result['Empfehlung']}")

        st.subheader("Evidenz / Referenzen (Top-Chunks)")
        render_evidence(st.session_state.evidence)

        st.subheader("JSON")
        st.code(json.dumps(st.session_state.result, ensure_ascii=False, indent=2), language="json")

        st.download_button(
            "JSON herunterladen",
            data=json.dumps(st.session_state.result, ensure_ascii=False, indent=2),
            file_name="entscheidung.json",
            mime="application/json"
        )
