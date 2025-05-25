
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("AMO Eiendom v48.2 – Robust og klar")

default = {
    "navn": "Eksempelveien 1",
    "prisantydning": 3500000.0,
    "kjøpesum": 3400000.0,
    "oppussing": 250000.0,
    "lån": 3000000.0,
    "rente": 5.0,
    "år": 25,
    "avdragsfri": 2,
    "lånetype": "Annuitetslån",
    "leie": 22000.0,
    "drift": 40000.0,
    "eierform": "Privat"
}

eiendom = st.session_state.get("eiendom", default)

with st.sidebar:
    st.header("Inndata")
    eiendom["navn"] = st.text_input("Eiendomsnavn", value=eiendom["navn"])
    eiendom["prisantydning"] = st.number_input("Prisantydning", value=eiendom["prisantydning"], step=10000.0, format="%.0f")
    eiendom["kjøpesum"] = st.number_input("Kjøpesum", value=eiendom["kjøpesum"], step=10000.0, format="%.0f")
    eiendom["oppussing"] = st.number_input("Oppussing", value=eiendom["oppussing"], step=10000.0, format="%.0f")
    eiendom["lån"] = st.number_input("Lånebeløp", value=eiendom["lån"], step=10000.0, format="%.0f")
    eiendom["rente"] = st.number_input("Rente (%)", value=eiendom["rente"], step=0.1, format="%.2f")
    eiendom["år"] = st.number_input("Løpetid (år)", value=eiendom["år"], step=1)
    eiendom["avdragsfri"] = st.number_input("Avdragsfri periode (år)", value=eiendom["avdragsfri"], step=1)
    eiendom["lånetype"] = st.selectbox("Lånetype", ["Annuitetslån", "Serielån"], index=0 if eiendom["lånetype"] == "Annuitetslån" else 1)
    eiendom["leie"] = st.number_input("Leie/mnd", value=eiendom["leie"], step=1000.0, format="%.0f")
    eiendom["drift"] = st.number_input("Driftskostnader/år", value=eiendom["drift"], step=1000.0, format="%.0f")
    eiendom["eierform"] = st.selectbox("Eierform", ["Privat", "AS"], index=0 if eiendom["eierform"] == "Privat" else 1)

    if st.button("Oppdater"):
        st.session_state.eiendom = eiendom

# Beregning
try:
    n = eiendom["år"] * 12
    af = eiendom["avdragsfri"] * 12
    r = eiendom["rente"] / 100 / 12
    saldo = eiendom["lån"]
    total = eiendom["kjøpesum"] + eiendom["oppussing"] + eiendom["kjøpesum"] * 0.025
    egenkapital = (total - eiendom["lån"]) / total * 100 if total > 0 else 0
    brutto_yield = (eiendom["leie"] * 12) / total * 100 if total > 0 else 0
    netto_yield = ((eiendom["leie"] * 12 - eiendom["drift"]) / total) * 100 if total > 0 else 0

    if eiendom["lånetype"] == "Annuitetslån" and r > 0:
        terminbeløp = saldo * (r * (1 + r)**(n - af)) / ((1 + r)**(n - af) - 1)
    else:
        terminbeløp = saldo / (n - af) if (n - af) > 0 else 0

    restgjeld, renter, cashflow, akk_cash = [], [], [], []
    saldo_løp = saldo
    akk = 0
    skatt = 0.3776 if eiendom["eierform"] == "AS" else 0

    for m in range(n):
        rente_mnd = saldo_løp * r
        if m < af:
            termin = rente_mnd
        elif eiendom["lånetype"] == "Serielån":
            avdrag = saldo / (n - af)
            termin = avdrag + rente_mnd
        else:
            avdrag = terminbeløp - rente_mnd
            termin = terminbeløp

        saldo_løp -= 0 if m < af else avdrag
        netto = eiendom["leie"] - eiendom["drift"] / 12 - termin
        netto -= netto * skatt if netto > 0 else 0
        akk += netto

        restgjeld.append(saldo_løp)
        renter.append(rente_mnd)
        cashflow.append(netto)
        akk_cash.append(akk)

    st.subheader(f"Resultater: {eiendom['navn']}")
    st.metric("Egenkapitalandel", f"{egenkapital:.1f}%")
    st.metric("Brutto yield", f"{brutto_yield:.2f}%")
    st.metric("Netto yield", f"{netto_yield:.2f}%")

    with st.expander("Grafer"):
        if st.checkbox("Restgjeld"):
            st.line_chart(restgjeld)
        if st.checkbox("Cashflow"):
            st.line_chart(cashflow)
        if st.checkbox("Akkumulert cashflow"):
            st.line_chart(akk_cash)
        if st.checkbox("Rentekostnader"):
            st.line_chart(renter)

except Exception as e:
    st.error(f"Feil i beregning: {e}")
