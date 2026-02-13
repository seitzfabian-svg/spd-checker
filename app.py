from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from src.parser import parse_document
from src.retrieval import build_retriever, retrieve_top_chunks
from src.llm import decide_with_llm
from src.render import render_decision_badge, render_sources

st.set_page_config(page_title="SPD Prozess-Checker", layout="wide")

st.title("SPD Prozess-Checker")

if "doc_text" not in st.session_state:
    st.session_state.doc_text = None
if "retriever" not in st.session_state:
    st.session_state.retriever = None
if "chunks" not in st.session_state:
    st.session_state.chunks = None
if "result" not in st.session_state:
    st.session_state.result = None

# Upload
st.header("1️⃣ SPD-Dokument hochladen")
uploaded = st.file_uploader("PDF oder TXT", type=["pdf", "txt"])

if uploaded:
    text = parse_document(uploaded)
    retriever, chunks = build_retriever(text)
    st.session_state.doc_text = text
    st.session_state.retriever = retriever
    st.session_state.chunks = chunks
    st.success("Dokument erfolgreich verarbeitet.")

# Input Formular
st.header("2️⃣ Inputvariablen")

with st.form("input_form"):
    amount = st.number_input("Betrag (EUR)", min_value=0.0, value=50.0)
    indication = st.text_input("Indikation")
    insured_status = st.selectbox("Versicherungsstatus", ["Mitglied", "Familienversichert", "Unklar"])
    prescription = st.selectbox("Ärztliche Verordnung", ["Ja", "Nein", "Unklar"])
    submit = st.form_submit_button("Prozess prüfen")

if submit:
    if not st.session_state.retriever:
        st.error("Bitte zuerst Dokument hochladen.")
    else:
        inputs = {
            "amount": amount,
            "indication": indication,
            "insured_status": insured_status,
            "prescription": prescription,
        }

        evidence = retrieve_top_chunks(
            st.session_state.retriever,
            st.session_state.chunks,
            str(inputs),
            top_k=5
        )

        result = decide_with_llm(inputs, evidence)
        st.session_state.result = result

# Ergebnis
st.header("3️⃣ Ergebnis")

if st.session_state.result:
    render_decision_badge(st.session_state.result["decision"])
    st.write("### Begründung")
    st.write(st.session_state.result["rationale"])

    st.write("### Referenzen")
    render_sources(st.session_state.result["evidence"])

    st.write("### JSON")
    st.json(st.session_state.result)
