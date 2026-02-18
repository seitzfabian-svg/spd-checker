import streamlit as st

def render_decision_badge(genehmigung: str):
    if genehmigung == "Ja":
        st.success("✅ Genehmigung: Ja")
    elif genehmigung == "Nein":
        st.error("⛔ Genehmigung: Nein")
    else:
        st.info("🧑‍⚖️ Genehmigung: Manuelle Prüfung")

def render_evidence(evidence_chunks):
    if not evidence_chunks:
        st.write("—")
        return

    for ev in evidence_chunks:
        cid = ev.get("chunk_id", "chunk")
        score = ev.get("score", None)
        title = f"{cid}" + (f" (score={score:.3f})" if isinstance(score, float) else "")
        with st.expander(title):
            st.write(ev.get("text", ""))
