import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --------- Konfigurasjon og stil ---------
st.set_page_config(layout="wide")
st.markdown("""
    <style>
    ::-webkit-scrollbar {
        width: 16px;
    }
    ::-webkit-scrollbar-thumb {
        background-color: #888;
        border-radius: 8px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background-color: #555;
    }
    </style>
""", unsafe_allow_html=True)
st.title("AMO Eiendom v48.5.6 – Lagre og slett fungerer riktig")

# --------- Passordbeskyttelse ---------
if "access_granted" not in st.session_state:
    pwd = st.text_input("Skriv inn passord for tilgang", type="password")
    if pwd == "amo123":
        st.session_state.access_granted = True
        st.experimental_rerun()
    else:
        st.stop()

# --------- Initialisering ---------
if "eiendommer" not in st.session_state:
    st.session_state.eiendommer = {}

# --------- Valg av eiendom ---------
valg_liste = ["(Ny eiendom)"] + list(st.session_state.eiendommer.keys())
valgt_navn = st.sidebar.selectbox("Velg eiendom", valg_liste)
er_ny = valgt_navn == "(Ny eiendom)"
data = st.session_state.eiendommer.get(valgt_navn, {}) if not er_ny else {}

# --------- Inndatafelt ---------
navn = st.sidebar.text_input("Navn på eiendom", value=valgt_navn if not er_ny else "")
finn_link = st.sidebar.text_input("Finn-lenke", value=data.get("finn", ""))
kjøpesum = st.sidebar.number_input("Kjøpesum", value=data.get("kjøpesum", 3000000.0), step=100000.0)

with st.sidebar.expander("Oppussing"):
    riving = st.number_input("Utrydding/riving", value=data.get("riving", 20000.0))
    bad = st.number_input("Bad", value=data.get("bad", 120000.0))
    kjøkken = st.number_input("Kjøkken", value=data.get("kjøkken", 100000.0))
    overflate = st.number_input("Overflate", value=data.get("overflate", 30000.0))
    gulv = st.number_input("Gulv/dører/lister", value=data.get("gulv", 40000.0))
    rørlegger = st.number_input("Rørlegger", value=data.get("rørlegger", 25000.0))
    elektriker = st.number_input("Elektriker", value=data.get("elektriker", 30000.0))
    utvendig = st.number_input("Utvendig", value=data.get("utvendig", 20000.0))

oppussing = sum([riving, bad, kjøkken, overflate, gulv, rørlegger, elektriker, utvendig])
st.sidebar.markdown(f"**Total oppussing:** {int(oppussing):,} kr")

leie = st.sidebar.number_input("Leieinntekter/mnd", value=data.get("leie", 22000.0))

with st.sidebar.expander("Driftskostnader per år"):
    forsikring = st.number_input("Forsikring", value=data.get("forsikring", 8000.0))
    strøm = st.number_input("Strøm", value=data.get("strøm", 12000.0))
    kommunale = st.number_input("Kommunale avg./felleskost.", value=data.get("kommunale", 9000.0))
    internett = st.number_input("Internett", value=data.get("internett", 3000.0))
    vedlikehold = st.number_input("Vedlikehold", value=data.get("vedlikehold", 8000.0))

drift = sum([forsikring, strøm, kommunale, internett, vedlikehold])
st.sidebar.markdown(f"**Totale driftskostnader:** {int(drift):,} kr")

lån = st.sidebar.number_input("Lån", value=data.get("lån", 2700000.0))
rente = st.sidebar.number_input("Rente (%)", value=data.get("rente", 5.0))
løpetid = st.sidebar.number_input("Løpetid (år)", value=data.get("løpetid", 25))
avdragsfri = st.sidebar.number_input("Avdragsfri (år)", value=data.get("avdragsfri", 2))
lånetype = st.sidebar.selectbox("Lånetype", ["Annuitetslån", "Serielån"], index=["Annuitetslån", "Serielån"].index(data.get("lånetype", "Annuitetslån")))
eierform = st.sidebar.radio(
    "Eierform", 
    ["Privat", "AS"], 
    index=["Privat", "AS"].index(data.get("eierform", "Privat"))
)


    st.line_chart(df[["Netto cashflow", "Akk. cashflow"]])
    st.line_chart(df[["Renter", "Avdrag"]])
    st.line_chart(df["Restgjeld"])
