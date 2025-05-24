
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("AMO Eiendom – Feilsikker versjon")

# Forsikre oss om at vi alltid har session state
if "eiendom" not in st.session_state:
    st.session_state.eiendom = {
        "navn": "Eksempelgård",
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

data = st.session_state.eiendom

try:
    n = data["år"] * 12
    af = data["avdragsfri"] * 12
    r = data["rente"] / 100 / 12
    saldo = data["lån"]
    total = data["kjøpesum"] + data["oppussing"] + data["kjøpesum"] * 0.025
    egenkapital = (total - data["lån"]) / total * 100 if total > 0 else 0
    brutto_yield = (data["leie"] * 12) / total * 100 if total > 0 else 0
    netto_yield = ((data["leie"] * 12 - data["drift"]) / total) * 100 if total > 0 else 0

    if data["lånetype"] == "Annuitetslån" and r > 0:
        terminbeløp = saldo * (r * (1 + r)**(n - af)) / ((1 + r)**(n - af) - 1)
    else:
        terminbeløp = saldo / (n - af) if (n - af) > 0 else 0

    restgjeld, avdrag, renter, cashflow, akk_cash = [], [], [], [], []
    saldo_løp = saldo
    akk = 0
    skatt = 0.3776 if data["eierform"] == "AS" else 0

    for m in range(n):
        rente_mnd = saldo_løp * r
        if m < af:
            avdrag_mnd = 0
            termin = rente_mnd
        elif data["lånetype"] == "Serielån":
            avdrag_mnd = saldo / (n - af)
            termin = avdrag_mnd + rente_mnd
        else:
            avdrag_mnd = terminbeløp - rente_mnd
            termin = terminbeløp

        saldo_løp -= avdrag_mnd
        netto = data["leie"] - data["drift"] / 12 - termin
        netto -= netto * skatt if netto > 0 else 0
        akk += netto

        restgjeld.append(saldo_løp)
        avdrag.append(avdrag_mnd)
        renter.append(rente_mnd)
        cashflow.append(netto)
        akk_cash.append(akk)

    st.subheader(f"Resultater for: {data['navn']}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Egenkapitalandel", f"{egenkapital:.1f} %")
    col2.metric("Brutto yield", f"{brutto_yield:.2f} %")
    col3.metric("Netto yield", f"{netto_yield:.2f} %")

    with st.expander("Vis grafer"):
        show1 = st.checkbox("Vis restgjeld")
        show2 = st.checkbox("Vis cashflow")
        show3 = st.checkbox("Vis akkumulert cashflow")
        show4 = st.checkbox("Vis rentekostnader")

        if show1:
            fig, ax = plt.subplots()
            ax.plot(restgjeld)
            ax.set_title("Restgjeld")
            st.pyplot(fig)

        if show2:
            fig2, ax2 = plt.subplots()
            ax2.plot(cashflow)
            ax2.set_title("Cashflow")
            st.pyplot(fig2)

        if show3:
            fig3, ax3 = plt.subplots()
            ax3.plot(akk_cash)
            ax3.set_title("Akkumulert Cashflow")
            st.pyplot(fig3)

        if show4:
            fig4, ax4 = plt.subplots()
            ax4.plot(renter)
            ax4.set_title("Renteutgifter")
            st.pyplot(fig4)

except Exception as e:
    st.error(f"Noe gikk galt i beregningene: {e}")
