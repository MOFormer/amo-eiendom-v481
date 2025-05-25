
# Fullt fungerende kode kommer her – inkludert alt fra 48.3.9 og 48.4
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("AMO Eiendom v48.5.1 – Alt i ett")

if "eiendommer" not in st.session_state:
    st.session_state.eiendommer = {}

with st.sidebar:
    st.header("Eiendom")
    navn = st.text_input("Navn på eiendom", "Eksempelveien 1")
    kjøpesum = st.number_input("Kjøpesum", value=3000000.0, step=100000.0)

    with st.expander("Oppussing"):
        riving = st.number_input("Utrydding/riving", value=20000.0)
        bad = st.number_input("Bad", value=120000.0)
        kjøkken = st.number_input("Kjøkken", value=100000.0)
        overflate = st.number_input("Overflate", value=30000.0)
        gulv = st.number_input("Gulv/dører/lister", value=40000.0)
        rørlegger = st.number_input("Rørlegger", value=25000.0)
        elektriker = st.number_input("Elektriker", value=30000.0)
        utvendig = st.number_input("Utvendig", value=20000.0)

    oppussing = sum([riving, bad, kjøkken, overflate, gulv, rørlegger, elektriker, utvendig])
    leie = st.number_input("Leieinntekter/mnd", value=22000.0)
    drift = st.number_input("Driftskostnader/år", value=36000.0)
    lån = st.number_input("Lån", value=2700000.0)
    rente = st.number_input("Rente (%)", value=5.0)
    løpetid = st.number_input("Løpetid (år)", value=25)
    avdragsfri = st.number_input("Avdragsfri (år)", value=2)
    lånetype = st.selectbox("Lånetype", ["Annuitetslån", "Serielån"])
    eierform = st.radio("Eierform", ["Privat", "AS"])
    vis_grafer = st.checkbox("Vis grafer", value=True)

    if st.button("Legg til eiendom"):
        st.session_state.eiendommer[navn] = {
            "kjøpesum": kjøpesum, "oppussing": oppussing, "leie": leie,
            "drift": drift, "lån": lån, "rente": rente,
            "løpetid": løpetid, "avdragsfri": avdragsfri,
            "lånetype": lånetype, "eierform": eierform
        }

if st.session_state.eiendommer:
    valgt = st.selectbox("Velg eiendom", list(st.session_state.eiendommer.keys()))
    data = st.session_state.eiendommer[valgt]

    # Beregning
    total = data["kjøpesum"] + data["oppussing"] + data["kjøpesum"] * 0.025
    n = int(data["løpetid"] * 12)
    af = int(data["avdragsfri"] * 12)
    r = data["rente"] / 100 / 12
    skatt = 0.0

    if data["lånetype"] == "Annuitetslån" and r > 0:
        terminbeløp = data["lån"] * (r * (1 + r)**(n - af)) / ((1 + r)**(n - af) - 1)
    else:
        terminbeløp = data["lån"] / (n - af) if (n - af) > 0 else 0

    restgjeld, avdrag, renter_liste, netto_cf, akk_cf = [], [], [], [], []
    saldo = data["lån"]
    akk = 0

    for m in range(n):
        rente_mnd = saldo * r
        if m < af:
            avdrag_mnd = 0
            termin = rente_mnd
        elif data["lånetype"] == "Serielån":
            avdrag_mnd = data["lån"] / (n - af)
            termin = avdrag_mnd + rente_mnd
        else:
            avdrag_mnd = terminbeløp - rente_mnd
            termin = terminbeløp

        saldo -= avdrag_mnd
        netto = data["leie"] - data["drift"] / 12 - termin
        if data["eierform"] == "AS" and netto > 0:
            netto -= netto * 0.375  # utbytteskatt
        akk += netto

        restgjeld.append(saldo)
        avdrag.append(avdrag_mnd)
        renter_liste.append(rente_mnd)
        netto_cf.append(netto)
        akk_cf.append(akk)

    st.subheader(f"Resultater for: {valgt}")
    st.metric("Total investering", f"{int(total):,} kr")
    st.metric("Brutto yield", f"{(data['leie'] * 12 / total) * 100:.2f} %")
    st.metric("Netto yield", f"{((data['leie'] * 12 - data['drift']) / total) * 100:.2f} %")

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
        st.line_chart(df[["Netto cashflow", "Akk. cashflow"]])
        st.line_chart(df[["Renter", "Avdrag"]])
        st.line_chart(df["Restgjeld"])
else:
    st.info("Legg til en eiendom for å starte.")
