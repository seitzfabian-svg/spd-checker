from dotenv import load_dotenv
load_dotenv()

import os
import json
import streamlit as st

from src.parser import parse_document
from src.retrieval import build_retriever, retrieve_top_chunks
from src.llm import decide_with_llm
from src.render import render_decision_badge, render_sources

st.set_page_config(page_title="SPD Prozess-Checker", layout="wide")

st.title("SPD Prozess-Checker (Doc-grounded)")
st.caption("Entscheidung basiert ausschließlich auf der hochgeladenen SPD-Dokumentation. Fehlt Evidenz → Manuelle Prüfung.")

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

# ----------------------------
# UI Layout
# ----------------------------
col_left, col_right = st.columns([0.48, 0.52], gap="large")

with col_left:
    st.header("1) SPD-Dokument hochladen")
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
        st.subheader("DWH-Abfrage (optional)")
        dwh_prev_treatment = st.radio(
            "Gab es bereits eine vorherige Behandlung?",
            ["Unklar", "Ja", "Nein"],
            index=0,
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
            st.error("Bitte zuerst eine SPD-Dokumentation hochladen.")
        else:
            inputs = {
                "extOrdnungsbegriff": extOrdnungsbegriff,
                "extLeistungsangebot": extLeistungsangebot,
                "extRechnungsbetrag": extRechnungsbetrag,
                "extRechnungsdatum": extRechnungsdatum,
                "extIBAN": extIBAN,
                "extBVEinmaligkeit": extBVEinmaligkeit,
                "sysQueueSelectorName": sysQueueSelectorName,
                "sysExternalId": sysExternalId,
                "extAbweichenderKontoinhaber": extAbweichenderKontoinhaber,
                "dwh": {
                    "previous_treatment": dwh_prev_treatment,  # "Ja" | "Nein" | "Unklar"
                    "total_refunded_eur": dwh_total_refunded
                }
            }

            evidence = retrieve_top_chunks(
                st.session_state.retriever,
                st.session_state.chunks,
                json.dumps(inputs, ensure_ascii=False),
                top_k=6
            )

            with st.spinner("Entscheidung wird geprüft (doc-grounded) ..."):
                try:
                    result = decide_with_llm(inputs, evidence)
                    st.session_state.result = result
                except Exception as e:
                    st.error(f"LLM-Entscheidung fehlgeschlagen: {e}")

with col_right:
    st.header("3) Ergebnis")

    if st.session_state.result is None:
        st.info("Noch keine Prüfung ausgeführt.")
    else:
        render_decision_badge(st.session_state.result.get("decision", "Manuelle Prüfung"))

        st.subheader("Begründung")
        st.write(st.session_state.result.get("rationale", ""))

        st.subheader("Referenzen / Evidenz")
        render_sources(st.session_state.result.get("evidence", []))

        st.subheader("JSON")
        st.json(st.session_state.result)

        st.download_button(
            "JSON herunterladen",
            data=json.dumps(st.session_state.result, ensure_ascii=False, indent=2),
            file_name="entscheidung.json",
            mime="application/json"
        )
