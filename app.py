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

# Hent eller sett default-verdier direkte i session_state (usynlig for brukeren)
defaults = {
    "riving": 20000,
    "bad": 120000,
    "kjøkken": 100000,
    "overflate": 30000,
    "gulv": 40000,
    "rørlegger": 25000,
    "elektriker": 30000,
    "utvendig": 20000,
    "test": 20000  
}

for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# Beregn totalen FØR expander vises
oppussing = sum([
    st.session_state["riving"],
    st.session_state["bad"],
    st.session_state["kjøkken"],
    st.session_state["overflate"],
    st.session_state["gulv"],
    st.session_state["rørlegger"],
    st.session_state["elektriker"],
    st.session_state["utvendig"],
    st.session_state["test"]
])

# ✅ Nå vises bare expander – og summen er i tittelen!
with st.sidebar.expander(f"🔨 Oppussing: {int(oppussing):,} kr"):
    st.session_state["riving"] = st.number_input("Riving", value=st.session_state["riving"])
    st.session_state["bad"] = st.number_input("Bad", value=st.session_state["bad"])
    st.session_state["kjøkken"] = st.number_input("Kjøkken", value=st.session_state["kjøkken"])
    st.session_state["overflate"] = st.number_input("Overflate", value=st.session_state["overflate"])
    st.session_state["gulv"] = st.number_input("Gulv/lister", value=st.session_state["gulv"])
    st.session_state["rørlegger"] = st.number_input("Rørlegger", value=st.session_state["rørlegger"])
    st.session_state["elektriker"] = st.number_input("Elektriker", value=st.session_state["elektriker"])
    st.session_state["utvendig"] = st.number_input("Utvendig", value=st.session_state["utvendig"])

# ------------------ Driftskostnader ------------------

# Hent eller sett default-verdier i session_state
drift_defaults = {
    "forsikring": 8000,
    "strøm": 12000,
    "kommunale": 9000,
    "internett": 3000,
    "vedlikehold": 8000
}

for key, val in drift_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# Beregn totalsum før expander vises
drift = sum([
    st.session_state["forsikring"],
    st.session_state["strøm"],
    st.session_state["kommunale"],
    st.session_state["internett"],
    st.session_state["vedlikehold"]
])

# ✅ Expander med totalsum i tittelen
with st.sidebar.expander(f"💡 Driftskostnader: {int(drift):,} kr"):
    st.session_state["forsikring"] = st.number_input("Forsikring", value=st.session_state["forsikring"])
    st.session_state["strøm"] = st.number_input("Strøm", value=st.session_state["strøm"])
    st.session_state["kommunale"] = st.number_input("Kommunale avgifter", value=st.session_state["kommunale"])
    st.session_state["internett"] = st.number_input("Internett", value=st.session_state["internett"])
    st.session_state["vedlikehold"] = st.number_input("Vedlikehold", value=st.session_state["vedlikehold"])

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
