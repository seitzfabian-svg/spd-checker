import streamlit as st

def render_decision_badge(decision):
    if decision == "Genehmigt":
        st.success("✅ Genehmigt")
    elif decision == "Abgelehnt":
        st.error("❌ Abgelehnt")
    elif decision == "Empfehlung":
        st.warning("⚠ Empfehlung")
    else:
        st.info("🧑‍⚖️ Manuelle Prüfung")

def render_sources(evidence):
    for ev in evidence:
        with st.expander("Dokumentstelle"):
            st.write(ev)
