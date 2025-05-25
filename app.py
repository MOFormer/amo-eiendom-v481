
import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("AMO Eiendom v48.4 – AS vs Privat og flere eiendommer")

if "eiendommer" not in st.session_state:
    st.session_state.eiendommer = {}

with st.sidebar:
    st.header("Eiendom")
    navn = st.text_input("Navn på eiendom", "Eksempelveien 1")
    kjøpesum = st.number_input("Kjøpesum", value=3000000.0, step=100000.0)
    oppussing = st.number_input("Oppussing", value=200000.0, step=10000.0)
    leie = st.number_input("Leie/mnd", value=22000.0, step=1000.0)
    drift = st.number_input("Driftskostnader/år", value=36000.0, step=1000.0)
    lån = st.number_input("Lån", value=2700000.0, step=100000.0)
    rente = st.number_input("Rente (%)", value=5.0, step=0.1)
    eierform = st.radio("Eierform", ["Privat", "AS"])

    if st.button("Legg til eiendom"):
        st.session_state.eiendommer[navn] = {
            "kjøpesum": kjøpesum,
            "oppussing": oppussing,
            "leie": leie,
            "drift": drift,
            "lån": lån,
            "rente": rente,
            "eierform": eierform
        }

if st.session_state.eiendommer:
    valgt = st.selectbox("Velg eiendom", list(st.session_state.eiendommer.keys()))
    data = st.session_state.eiendommer[valgt]

    total = data["kjøpesum"] + data["oppussing"] + data["kjøpesum"] * 0.025
    brutto = data["leie"] * 12
    netto = brutto - data["drift"]

    if data["eierform"] == "AS":
        utbytteskatt = 0.375
        netto_as = netto * (1 - utbytteskatt)
    else:
        netto_as = netto

    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"Privat")
        st.metric("Netto cashflow", f"{netto:,.0f} kr")
    with col2:
        st.subheader(f"AS")
        st.metric("Netto etter utbytte", f"{netto_as:,.0f} kr")

    st.success("Beregning fullført")

else:
    st.info("Legg til en eiendom for å begynne.")
