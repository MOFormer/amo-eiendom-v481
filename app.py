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

# --------------------------
# Kjøpesum og kjøpskostnader
# --------------------------
kjøpesum = st.sidebar.number_input("Kjøpesum", value=3000000, step=100000, key="kjøpesum")
kjøpskostnader = kjøpesum * 0.025

# ------------------ Input ------------------
st.sidebar.header("Eiendomsinfo")
kjøpesum = st.sidebar.number_input("Kjøpesum", value=3_000_000, step=100_000)
leie = st.sidebar.number_input("Leieinntekter / mnd", value=22_000)

# ------------------ Oppussing ------------------

# --------------------------
# Oppussing standardverdier
# --------------------------
oppussing_defaults = {
    "riving": 20000,
    "bad": 120000,
    "kjøkken": 100000,
    "overflate": 30000,
    "gulv": 40000,
    "rørlegger": 25000,
    "elektriker": 30000,
    "utvendig": 20000,
}

# --------------------------
# Init session state
# --------------------------
if "oppussing_values" not in st.session_state:
    st.session_state["oppussing_values"] = oppussing_defaults.copy()

if "oppussing_reset_trigger" not in st.session_state:
    st.session_state["oppussing_reset_trigger"] = False

if st.session_state["oppussing_reset_trigger"]:
    for key in oppussing_defaults:
        st.session_state["oppussing_values"][key] = 0
    st.session_state["oppussing_reset_trigger"] = False

# ------------------ OPPUSSING UI ------------------

# --------------------------
# Sidebar UI - Oppussing
# --------------------------
st.sidebar.title("Eiendomskalkulator")

# Kalkuler totalsum først
oppussing_total = sum(st.session_state["oppussing_values"].values())

with st.sidebar.expander(f"🔨 Oppussing: {int(oppussing_total):,} kr"):
    for key in oppussing_defaults:
        val = st.number_input(
            label=key.capitalize(),
            value=st.session_state["oppussing_values"][key],
            key=f"opp_{key}"
        )
        st.session_state["oppussing_values"][key] = val

    if st.button("Tilbakestill oppussing"):
        st.session_state["oppussing_reset_trigger"] = True

# --------------------------
# Total investering
# --------------------------
total_investering = kjøpesum + oppussing_total + kjøpskostnader

st.subheader("✨ Resultat")
st.metric("Total investering", f"{int(total_investering):,} kr")


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

# ------------------ Lån og finansiering ------------------

# Sett standardverdier i session_state
lån_defaults = {
    "egenkapital": 300000,
    "rente": 5.0,
    "løpetid": 25,
    "avdragsfri": 2,
    "lånetype": "Annuitetslån",
    "eierform": "Privat"
}

for key, val in lån_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# Beregn lånebeløp fra kjøpesum og oppussing (hentet fra tidligere i appen)
kjøpskostnader = st.session_state.get("kjøpskostnader", 0)
total_investering = st.session_state.get("total_investering", 3_000_000 + 500_000 + 75_000)  # fallback
lånebeløp = total_investering - st.session_state["egenkapital"]

# Lagre beregnet lånebeløp
st.session_state["lån"] = lånebeløp

# ✅ Expander med lånebeløp i tittel
with st.sidebar.expander(f"🏦 Lån: {int(st.session_state['lån']):,} kr"):

    st.session_state["egenkapital"] = st.number_input(
        "Egenkapital", value=st.session_state["egenkapital"], min_value=0
    )

    # Oppdater lånebeløp når egenkapital endres
    st.session_state["lån"] = total_investering - st.session_state["egenkapital"]

    st.session_state["rente"] = st.number_input("Rente (%)", value=st.session_state["rente"], step=0.1)
    st.session_state["løpetid"] = st.number_input("Løpetid (år)", value=st.session_state["løpetid"], step=1)
    st.session_state["avdragsfri"] = st.number_input("Avdragsfri (år)", value=st.session_state["avdragsfri"], step=1)
    st.session_state["lånetype"] = st.selectbox("Lånetype", ["Annuitetslån", "Serielån"], 
                                                index=["Annuitetslån", "Serielån"].index(st.session_state["lånetype"]))
    st.session_state["eierform"] = st.radio("Eierform", ["Privat", "AS"], 
                                             index=["Privat", "AS"].index(st.session_state["eierform"]))

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
total_investering = kjøpesum + oppussing_total + kjøpskostnader
df, akk = beregn_lån(
    st.session_state["lån"],
    st.session_state["rente"],
    st.session_state["løpetid"],
    st.session_state["avdragsfri"],
    st.session_state["lånetype"],
    leie,
    drift,
    st.session_state["eierform"]
)

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
