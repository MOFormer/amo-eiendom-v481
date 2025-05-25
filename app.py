
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("AMO Eiendom v48.3.9 – Grafer og Oppussing")

try:
    with st.sidebar:
        st.header("Eiendomsdata")
        navn = st.text_input("Navn", "Eksempelveien 1")
        kjøpesum = st.number_input("Kjøpesum", value=3000000.0, step=100000.0)
        st.subheader("Oppussing")
        with st.expander("Oppussingskostnader"):
            riving = st.number_input("Utrydding/riving", value=20000.0, step=1000.0)
            bad = st.number_input("Bad", value=120000.0, step=1000.0)
            kjøkken = st.number_input("Kjøkken", value=100000.0, step=1000.0)
            overflate = st.number_input("Overflate (maling/sparkling)", value=30000.0, step=1000.0)
            gulv = st.number_input("Gulv/dører/lister", value=40000.0, step=1000.0)
            rørlegger = st.number_input("Rørlegger", value=25000.0, step=1000.0)
            elektriker = st.number_input("Elektriker", value=30000.0, step=1000.0)
            utvendig = st.number_input("Utvendig", value=20000.0, step=1000.0)

        oppussing = sum([riving, bad, kjøkken, overflate, gulv, rørlegger, elektriker, utvendig])
        st.write(f"**Total oppussing:** {int(oppussing):,} kr")

        leie = st.number_input("Leie per måned", value=22000.0, step=1000.0)
        drift = st.number_input("Årlige driftskostnader", value=36000.0, step=1000.0)

        st.header("Lån")
        lån = st.number_input("Lånebeløp", value=2700000.0, step=100000.0)
        rente = st.number_input("Rente (%)", value=5.0, step=0.1)
        løpetid = st.number_input("Løpetid (år)", value=25, step=1)
        avdragsfri = st.number_input("Avdragsfri periode (år)", value=2, step=1)
        lånetype = st.selectbox("Lånetype", ["Annuitetslån", "Serielån"])
        vis_grafer = st.checkbox("Vis grafer", value=True)

    total = kjøpesum + oppussing + kjøpesum * 0.025
    n = int(løpetid * 12)
    af = int(avdragsfri * 12)
    r = rente / 100 / 12
    skatt = 0

    if lånetype == "Annuitetslån" and r > 0:
        terminbeløp = lån * (r * (1 + r)**(n - af)) / ((1 + r)**(n - af) - 1)
    else:
        terminbeløp = lån / (n - af) if (n - af) > 0 else 0

    restgjeld, avdrag, renter_liste, netto_cf, akk_cf = [], [], [], [], []
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
        renter_liste.append(rente_mnd)
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
        "Renter": renter_liste,
        "Netto cashflow": netto_cf,
        "Akk. cashflow": akk_cf
    })

    st.dataframe(df.head(60))

    if vis_grafer:
        st.subheader("Grafer")
        st.line_chart(df[["Netto cashflow", "Akk. cashflow"]])
        st.line_chart(df[["Renter", "Avdrag"]])
        st.line_chart(df["Restgjeld"])

    st.success("Beregning OK!")

except Exception as e:
    st.error(f"Feil i beregning eller visning: {e}")
