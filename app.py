
import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("AMO Eiendom v48.3.8 – Cashflow og Lånebetingelser")

try:
    with st.sidebar:
        st.header("Eiendomsdata")
        navn = st.text_input("Navn", "Eksempelveien 1")
        kjøpesum = st.number_input("Kjøpesum", value=3000000.0, step=100000.0)
        oppussing = st.number_input("Oppussing", value=200000.0, step=10000.0)
        leie = st.number_input("Leie per måned", value=22000.0, step=1000.0)
        drift = st.number_input("Årlige driftskostnader", value=36000.0, step=1000.0)

        st.header("Lån")
        lån = st.number_input("Lånebeløp", value=2700000.0, step=100000.0)
        rente = st.number_input("Rente (%)", value=5.0, step=0.1)
        løpetid = st.number_input("Løpetid (år)", value=25, step=1)
        avdragsfri = st.number_input("Avdragsfri periode (år)", value=2, step=1)
        lånetype = st.selectbox("Lånetype", ["Annuitetslån", "Serielån"])

    st.success("Input OK")

    total = kjøpesum + oppussing + kjøpesum * 0.025
    n = int(løpetid * 12)
    af = int(avdragsfri * 12)
    r = rente / 100 / 12
    skatt = 0  # forenklet

    if lånetype == "Annuitetslån" and r > 0:
        terminbeløp = lån * (r * (1 + r)**(n - af)) / ((1 + r)**(n - af) - 1)
    else:
        terminbeløp = lån / (n - af) if (n - af) > 0 else 0

    restgjeld, avdrag, renter, netto_cf, akk_cf = [], [], [], [], []
    saldo = lån
    akk = 0

    for m in range(n):
        rente_mnd = saldo * r
        if m < af:
            avdrag_mnd = 0
            termin = rente_mnd
        elif lånetype == "Serielån":
            avdrag_mnd = lån / (n - af)
            termin = avdrag_mnd + rente_mnd
        else:
            avdrag_mnd = terminbeløp - rente_mnd
            termin = terminbeløp

        saldo -= avdrag_mnd
        netto = leie - drift / 12 - termin
        netto -= netto * skatt if netto > 0 else 0
        akk += netto

        restgjeld.append(saldo)
        avdrag.append(avdrag_mnd)
        renter.append(rente_mnd)
        netto_cf.append(netto)
        akk_cf.append(akk)

    st.subheader(f"Resultater for: {navn}")
    st.metric("Total investering", f"{int(total):,} kr")
    st.metric("Brutto yield", f"{(leie * 12 / total) * 100:.2f} %")
    st.metric("Netto yield", f"{((leie * 12 - drift) / total) * 100:.2f} %")

    df = pd.DataFrame({
        "Måned": list(range(1, n + 1)),
        "Restgjeld": restgjeld,
        "Avdrag": avdrag,
        "Renter": renter,
        "Netto cashflow": netto_cf,
        "Akk. cashflow": akk_cf
    })

    st.success("Beregning OK – viser tabell")
    st.dataframe(df.head(60))

except Exception as e:
    st.error(f"Feil i beregning: {e}")
