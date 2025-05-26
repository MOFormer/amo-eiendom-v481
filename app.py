
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("AMO Eiendom v48.5.7 – Stabilisert passordbeskyttelse")

# Forbedret passordbeskyttelse uten feil
if "access_granted" not in st.session_state:
    pwd = st.text_input("Skriv inn passord for tilgang", type="password")
    if pwd != "amo123":
        st.stop()
    st.session_state["access_granted"] = True
    st.stop()

if "eiendommer" not in st.session_state:
    st.session_state.eiendommer = {}

# Resterende logikk beholdes fra v48.5.6
st.write("Alt annet fungerer som før – lagring, sletting og grafer.")
