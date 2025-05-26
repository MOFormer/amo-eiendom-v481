
import streamlit as st

st.set_page_config(layout="wide")
st.title("AMO Eiendom v48.5.9 – Klar for ny Streamlit-versjon")

# Trygg passordhåndtering med st.rerun()
if "access_granted" not in st.session_state:
    pwd = st.text_input("Skriv inn passord for tilgang", type="password")
    if pwd != "amo123":
        st.stop()
    st.session_state.access_granted = True
    st.rerun()

st.success("Du er logget inn! Appen fungerer nå uten feil.")
st.write("Resten av eiendomsverktøyet vises her.")
