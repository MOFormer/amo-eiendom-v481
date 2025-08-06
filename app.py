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

# --------- Oppussing ---------
# Midlertidige inputs for summering før expanderen
_riv = st.sidebar.number_input("🔨 Riving", value=20_000, key="riving_sum_calc")
_bad = st.sidebar.number_input("🔨 Bad", value=120_000, key="bad_sum_calc")
_kjøkken = st.sidebar.number_input("🔨 Kjøkken", value=100_000, key="kjøkken_sum_calc")
_overflate = st.sidebar.number_input("🔨 Overflate", value=30_000, key="overflate_sum_calc")
_gulv = st.sidebar.number_input("🔨 Gulv", value=40_000, key="gulv_sum_calc")
_rør = st.sidebar.number_input("🔨 Rørlegger", value=25_000, key="rør_sum_calc")
_el = st.sidebar.number_input("🔨 Elektriker", value=30_000, key="el_sum_calc")
_utv = st.sidebar.number_input("🔨 Utvendig", value=20_000, key="utv_sum_calc")
# Skjul dem etter summering
for k in ["riving_sum_calc", "bad_sum_calc", "kjøkken_sum_calc", "overflate_sum_calc",
          "gulv_sum_calc", "rør_sum_calc", "el_sum_calc", "utv_sum_calc"]:
    st.session_state.pop(k, None)

oppussing_sum = sum([_riv, _bad, _kjøkken, _overflate, _gulv, _rør, _el, _utv])
st.sidebar.markdown(f"**🔨 Oppussing: {int(oppussing_sum):,} kr**")

# --------- Driftskostnader med expander ---------
with st.sidebar.expander("💡 Driftskostnader per år"):
    forsikring = st.number_input("Forsikring", value=8_000)
    strøm = st.number_input("Strøm", value=12_000)
    kommunale = st.number_input("Kommunale avgifter", value=9_000)
    internett = st.number_input("Internett", value=3_000)
    vedlikehold = st.number_input("Vedlikehold", value=8_000)

drift = sum([forsikring, strøm, kommunale, internett, vedlikehold])

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
