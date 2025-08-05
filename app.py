import streamlit as st
import pandas as pd

# ------------------ Layout og stil ------------------
st.set_page_config(layout="wide")
st.markdown("""
    <style>
    .scroll-container {
        max-height: 400px;
        overflow-y: auto;
    }
    .scroll-container::-webkit-scrollbar {
        width: 50px;
    }
    .scroll-container::-webkit-scrollbar-thumb {
        background-color: #888;
        border-radius: 50px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("Eiendomskalkulator")

# ------------------ Input ------------------
st.sidebar.header("Eiendomsinfo")
kjøpesum = st.sidebar.number_input("Kjøpesum", value=3_000_000, step=100_000)
leie = st.sidebar.number_input("Leieinntekter / mnd", value=22_000)

st.sidebar.header("Oppussing")
riving = st.sidebar.number_input("Riving", value=20_000)
bad = st.sidebar.number_input("Bad", value=120_000)
kjøkken = st.sidebar.number_input("Kjøkken", value=100_000)
gulv = st.sidebar.number_input("Gulv og lister", value=40_000)
oppussing = riving + bad + kjøkken + gulv

st.sidebar.header("Driftskostnader (årlig)")
drift = sum([
    st.sidebar.number_input("Forsikring", value=8_000),
    st.sidebar.number_input("Strøm", value=12_000),
    st.sidebar.number_input("Kommunale avgifter", value=9_000),
    st.sidebar.number_input("Internett", value=3_000),
    st.sidebar.number_input("Vedlikehold", value=8_000),
])

st.sidebar.header("Lån")
lån = st.sidebar.number_input("Lånebeløp", value=2_700_000)
rente = st.sidebar.number_input("Rente (%)", value=5.0)
løpetid = st.sidebar.number_input("Løpetid (år)", value=25)
avdragsfri = st.sidebar.number_input("Avdragsfri (år)", value=2)
lånetype = st.sidebar.selectbox("Lånetype", ["Annuitetslån", "Serielån"])
eierform = st.sidebar.radio("Eierform", ["Privat", "AS"])

# ------------------ Kalkulasjon ------------------
def beregn_lån(lån, rente, løpetid, avdragsfri, lånetype, leie, drift, eierform):
    n = int(løpetid * 12)
    af = int(avdragsfri * 12)
    r = rente / 100 / 12

    if lånetype == "Annuitetslån" and r > 0:
        terminbeløp = lån * (r * (1 + r)**(n - af)) / ((1 + r)**(n - af) - 1)
    else:
        terminbeløp = lån / (n - af) if (n - af) > 0 else 0

    saldo = lån
    restgjeld, avdrag, renter_liste, netto_cf, akk_cf = [], [], [], [], []
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
        netto = leie - (drift / 12) - termin
        if eierform == "AS" and netto > 0:
            netto *= (1 - 0.375)
        akk += netto

        restgjeld.append(saldo)
        avdrag.append(avdrag_mnd)
        renter_liste.append(rente_mnd)
        netto_cf.append(netto)
        akk_cf.append(akk)

    df = pd.DataFrame({
        "Måned": list(range(1, n + 1)),
        "Restgjeld": restgjeld,
        "Avdrag": avdrag,
        "Renter": renter_liste,
        "Netto cashflow": netto_cf,
        "Akk. cashflow": akk_cf
    })

    return df, akk

# ------------------ Beregning ------------------
kjøpskostnader = kjøpesum * 0.025
total_investering = kjøpesum + oppussing + kjøpskostnader
df, akk = beregn_lån(lån, rente, løpetid, avdragsfri, lånetype, leie, drift, eierform)

# ------------------ Resultater ------------------
st.subheader("Resultater")
st.metric("Total investering", f"{int(total_investering):,} kr")
st.metric("Brutto yield", f"{(leie * 12 / total_investering) * 100:.2f} %")
st.metric("Netto yield", f"{((leie * 12 - drift) / total_investering) * 100:.2f} %")

# ------------------ Tabellvisning med bred scrollbar ------------------
st.subheader("Kontantstrøm (første 60 måneder)")
st.markdown('<div class="scroll-container">', unsafe_allow_html=True)
st.table(df.head(60))
st.markdown('</div>', unsafe_allow_html=True)

# ------------------ Grafer ------------------
st.subheader("Grafer")
st.line_chart(df[["Netto cashflow", "Akk. cashflow"]])
st.line_chart(df[["Renter", "Avdrag"]])
st.line_chart(df["Restgjeld"])
