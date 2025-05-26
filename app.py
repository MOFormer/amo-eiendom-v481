
import streamlit as st

st.set_page_config(layout="wide")
st.title("AMO Eiendom v48.5.8 – Trygg passordhåndtering")

# Trygg kombinasjon av state og rerun
if "access_granted" not in st.session_state:
    pwd = st.text_input("Skriv inn passord for tilgang", type="password")
    if pwd != "amo123":
        st.stop()
    st.session_state.access_granted = True
    st.experimental_rerun()

st.success("Du er logget inn og appen fungerer som den skal!")
st.write("Videre funksjoner som eiendommer, grafer og kalkyler vises her.")
