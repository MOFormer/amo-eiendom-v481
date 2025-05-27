
import streamlit as st

st.set_page_config(layout="wide")
st.title("AMO Eiendom v49.2.19")

# Dette er kun en forenklet placeholder - full appkode bør her inkludere:
# - Eiendomsvalg og lagring
# - Nedtrekksmenyer for oppussing og kostnader
# - Annuitet/serie/avdragsfri lån
# - Beregning av renter, avdrag, total cashflow
# - AS vs privat visning
# - Grafer og tabeller

# Eksempel på videre utvidelse:
if "kjøpesum" not in st.session_state:
    st.session_state.kjøpesum = 0.0

st.sidebar.header("Eiendomsdata")
st.sidebar.number_input("Kjøpesum", key="kjøpesum", step=100000.0, format="%.0f")

st.write(f"Registrert kjøpesum: {st.session_state.kjøpesum}")
