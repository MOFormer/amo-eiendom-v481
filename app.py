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
kjøpesum = st.sidebar.number_input("Kjøpesum", value=4_000_000, step=100_000)
kjøpskostnader = kjøpesum * 0.025
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
# Init input-verdier i session_state og reset trigger
# --------------------------
if "reset_oppussing_triggered" not in st.session_state:
    st.session_state["reset_oppussing_triggered"] = False

for key, default in oppussing_defaults.items():
    widget_key = f"opp_{key}"
    if widget_key not in st.session_state or st.session_state["reset_oppussing_triggered"]:
        st.session_state[widget_key] = 0 if st.session_state["reset_oppussing_triggered"] else default

# Nullstill flagget etter reset
if st.session_state["reset_oppussing_triggered"]:
    st.session_state["reset_oppussing_triggered"] = False

    
# ------------------ OPPUSSING UI ------------------

# --------------------------
# Oppussing UI i sidebar
# --------------------------
with st.sidebar.expander("🔨 Oppussing", expanded=True):
    total = 0
    for key in oppussing_defaults:
        widget_key = f"opp_{key}"
        val = st.number_input(
            label=key.capitalize(),
            value=st.session_state[widget_key],
            key=widget_key,
            step=1000,
            format="%d"
        )
        total += val

    st.markdown(f"**Totalt: {int(total):,} kr**")

    if st.button("Tilbakestill oppussing", key="reset_oppussing"):
        st.session_state["reset_oppussing_triggered"] = True
        st.rerun()

# --------------------------
# Kjøpesum og kjøpskostnader
# --------------------------
kjøpesum = st.sidebar.number_input("Kjøpesum", value=3000000, step=100000, key="kjøpesum")
kjøpskostnader = kjøpesum * 0.025

# --------------------------
# Total investering
# --------------------------
oppussing_total = sum(st.session_state[f"opp_{key}"] for key in oppussing_defaults)
total_investering = kjøpesum + oppussing_total + kjøpskostnader

st.subheader("✨ Resultat")
st.metric("Total investering", f"{int(total_investering):,} kr")



# ------------------ Driftskostnader ------------------

# --------------------------
# Driftskostnader standardverdier
# --------------------------
driftskostnader_defaults = {
    "forsikring": 8000,
    "strøm": 12000,
    "kommunale avgifter": 9000,
    "internett": 3000,
    "vedlikehold": 8000,
}

# --------------------------
# Driftskostnader UI i sidebar
# --------------------------
with st.sidebar.expander("📈 Driftskostnader", expanded=True):
    drift_total = 0
    for key, default in driftskostnader_defaults.items():
    widget_key = f"drift_{key}"
    if widget_key not in st.session_state:
        st.session_state[widget_key] = default

    val = st.number_input(
        label=key.capitalize(),
        value=st.session_state[widget_key],
        key=widget_key,
        step=1000,
        format="%d"
    )
    drift_total += val

    st.markdown(f"**Totalt: {int(drift_total):,} kr**")

    if st.button("Tilbakestill driftskostnader", key="reset_drift"):
        st.session_state["reset_drift_triggered"] = True
        st.rerun()

# --------------------------
# Kjøpesum og kjøpskostnader
# --------------------------
kjøpesum = st.sidebar.number_input("Kjøpesum", value=3000000, step=100000, key="kjøpesum")
kjøpskostnader = kjøpesum * 0.025

# --------------------------
# Total investering
# --------------------------
oppussing_total = sum(st.session_state[f"opp_{key}"] for key in oppussing_defaults)
total_investering = kjøpesum + oppussing_total + kjøpskostnader

st.subheader("✨ Resultat")
st.metric("Total investering", f"{int(total_investering):,} kr")


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
