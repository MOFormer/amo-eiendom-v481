import streamlit as st
import pandas as pd

# ------------------ Layout og stil ------------------
st.set_page_config(layout="wide")
st.markdown("""
    <style>
    /* Gjør scrollbaren mer synlig */
    div[data-testid="stDataFrameScrollable"]::-webkit-scrollbar {
        width: 50px;
    }

    div[data-testid="stDataFrameScrollable"]::-webkit-scrollbar-thumb {
        background-color: #444;
        border-radius: 50px;
    }

    div[data-testid="stDataFrameScrollable"]::-webkit-scrollbar-thumb:hover {
        background-color: #222;
    }
    </style>
""", unsafe_allow_html=True)

st.title("Eiendomskalkulator – med synlig scrollbar")

# ------------------ Input ------------------
st.sidebar.header("Eiendomsinfo")
kjøpesum = st.sidebar.number_input("Kjøpesum", value=3_000_000, step=100_000)
leie = st.sidebar.number_input("Leieinntekter / mnd", value=22_000)

# ------------------ Oppussing ------------------

# Midlertidige inputs for å kunne beregne summen først
_riving = st.sidebar.number_input("Riving", value=20000, key="r1_temp", label_visibility="collapsed")
_bad = st.sidebar.number_input("Bad", value=120000, key="r2_temp", label_visibility="collapsed")
_kjøkken = st.sidebar.number_input("Kjøkken", value=100000, key="r3_temp", label_visibility="collapsed")
_overflate = st.sidebar.number_input("Overflate", value=30000, key="r4_temp", label_visibility="collapsed")
_gulv = st.sidebar.number_input("Gulv/lister", value=40000, key="r5_temp", label_visibility="collapsed")
_rør = st.sidebar.number_input("Rørlegger", value=25000, key="r6_temp", label_visibility="collapsed")
_el = st.sidebar.number_input("Elektriker", value=30000, key="r7_temp", label_visibility="collapsed")
_utv = st.sidebar.number_input("Utvendig", value=20000, key="r8_temp", label_visibility="collapsed")

# Beregn totalsum før expander
oppussing = sum([_riving, _bad, _kjøkken, _overflate, _gulv, _rør, _el, _utv])

# Nå vis expander med riktig tittel
with st.sidebar.expander(f"🔨 Oppussing: {int(oppussing):,} kr"):
    riving = st.number_input("Riving", value=_riving, key="r1")
    bad = st.number_input("Bad", value=_bad, key="r2")
    kjøkken = st.number_input("Kjøkken", value=_kjøkken, key="r3")
    overflate = st.number_input("Overflate", value=_overflate, key="r4")
    gulv = st.number_input("Gulv/lister", value=_gulv, key="r5")
    rørlegger = st.number_input("Rørlegger", value=_rør, key="r6")
    elektriker = st.number_input("Elektriker", value=_el, key="r7")
    utvendig = st.number_input("Utvendig", value=_utv, key="r8")

# --------- Driftskostnader ---------
with st.sidebar.expander("💡 Driftskostnader"):
    forsikring = st.number_input("Forsikring", value=8_000)
    strøm = st.number_input("Strøm", value=12_000)
    kommunale = st.number_input("Kommunale avgifter", value=9_000)
    internett = st.number_input("Internett", value=3_000)
    vedlikehold = st.number_input("Vedlikehold", value=8_000)

drift = sum([forsikring, strøm, kommunale, internett, vedlikehold])

# ✅ Vis summering
st.sidebar.markdown(f"**💡 Driftskostnader: {int(drift):,} kr**")

# --------- Lån med expander ---------
with st.sidebar.expander("🏦 Lån og finansiering"):
    lån = st.number_input("Lånebeløp", value=2_700_000)
    rente = st.number_input("Rente (%)", value=5.0)
    løpetid = st.number_input("Løpetid (år)", value=25)
    avdragsfri = st.number_input("Avdragsfri (år)", value=2)
    lånetype = st.selectbox("Lånetype", ["Annuitetslån", "Serielån"])
    eierform = st.radio("Eierform", ["Privat", "AS"])

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

# ------------------ Scrollbar (synlig) med st.dataframe ------------------
st.subheader("Kontantstrøm (første 60 måneder)")
st.dataframe(df.head(60), use_container_width=True, height=500)

# ------------------ Grafer ------------------
st.subheader("Grafer")
st.line_chart(df[["Netto cashflow", "Akk. cashflow"]])
st.line_chart(df[["Renter", "Avdrag"]])
st.line_chart(df["Restgjeld"])
