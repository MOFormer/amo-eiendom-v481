import streamlit as st
import pandas as pd

# ------------------ Layout og stil ------------------
st.set_page_config(layout="wide")
st.markdown("""
    <style>
    /* Gjør scrollbaren mer synlig for dataframe */
    div[data-testid="stDataFrameScrollable"]::-webkit-scrollbar { width: 16px; }
    div[data-testid="stDataFrameScrollable"]::-webkit-scrollbar-thumb {
        background-color: #444; border-radius: 8px;
    }
    div[data-testid="stDataFrameScrollable"]::-webkit-scrollbar-thumb:hover { background-color: #222; }
    </style>
""", unsafe_allow_html=True)

st.title("Eiendomskalkulator – med synlig scrollbar")

# ------------------ Sidebar: grunninntasting ------------------
st.sidebar.header("🧾 Eiendomsinfo")
kjøpesum = st.sidebar.number_input("Kjøpesum", value=4_000_000, step=100_000)
leie = st.sidebar.number_input("Leieinntekter / mnd", value=22_000)
kjøpskostnader = kjøpesum * 0.025  # 2.5 % kjøpsomkostninger

# ===========================
# OPPUSSING (RERUN-FREE, ROBUST)
# ===========================
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

def _sum_section(prefix: str, defaults: dict, ns: int, zero_mode: bool) -> int:
    """Summerer verdier for en seksjon før UI rendres.
    Bruker eksisterende widget-keys hvis de finnes, ellers defaults.
    Returnerer heltall for pen tittel.
    """
    if zero_mode:
        return 0
    total = 0
    for key, default in defaults.items():
        wkey = f"{prefix}_{key}_{ns}"
        total += st.session_state.get(wkey, default)
    return int(total)

def sum_namespace(prefix: str, defaults: dict, ns: int) -> int:
    total = 0
    for key in defaults:
        wkey = f"{prefix}_{key}_{ns}"
        total += int(st.session_state.get(wkey, 0) or 0)
    return total

def sum_namespace(prefix: str, defaults: dict, ns: int) -> int:
    s = 0
    for k in defaults:
        s += int(st.session_state.get(f"{prefix}_{k}_{ns}", 0) or 0)
    return s

# --- Oppussing: pre-reset (må være før UI) ---
if "opp_ns" not in st.session_state:
    st.session_state["opp_ns"] = 0
if "opp_zero_mode" not in st.session_state:
    st.session_state["opp_zero_mode"] = False
if "opp_pending_reset" not in st.session_state:
    st.session_state["opp_pending_reset"] = False

if st.session_state["opp_pending_reset"]:
    st.session_state["opp_ns"] += 1
    st.session_state["opp_zero_mode"] = True
    st.session_state["opp_pending_reset"] = False  # konsumert

# --- Drift: pre-reset (må være før UI) ---
if "drift_ns" not in st.session_state:
    st.session_state["drift_ns"] = 0
if "drift_zero_mode" not in st.session_state:
    st.session_state["drift_zero_mode"] = False
if "drift_pending_reset" not in st.session_state:
    st.session_state["drift_pending_reset"] = False

if st.session_state["drift_pending_reset"]:
    st.session_state["drift_ns"] += 1
    st.session_state["drift_zero_mode"] = True
    st.session_state["drift_pending_reset"] = False  # konsumert

# ===========================
# 🔨 Oppussing (instant reset uten rerun)
# ===========================
# Init namespace
if "opp_ns" not in st.session_state:
    st.session_state["opp_ns"] = 0

# Reset-knapp MÅ komme før expanderen
if st.sidebar.button("Tilbakestill oppussing", key="btn_reset_opp"):
    st.session_state["opp_ns"] += 1

ns_opp = st.session_state["opp_ns"]
opp_title_total = sum_namespace("opp", oppussing_defaults, ns_opp)

with st.sidebar.expander(f"🔨 Oppussing: {opp_title_total:,} kr", expanded=True):
    oppussing_total = 0
    for key, default in oppussing_defaults.items():
        wkey = f"opp_{key}_{ns_opp}"
        startverdi = st.session_state.get(wkey, 0 if ns_opp > 0 else default)
        val = st.number_input(key.capitalize(), value=startverdi, key=wkey, step=1000, format="%d")
        oppussing_total += val
    st.markdown(f"**Totalt: {int(oppussing_total):,} kr**")


# ===========================
# DRIFTSKOSTNADER (RERUN-FREE, ROBUST)
# ===========================
driftskostnader_defaults = {
    "forsikring": 8000,
    "strøm": 12000,
    "kommunale avgifter": 9000,
    "internett": 3000,
    "vedlikehold": 8000,
}

# ===========================
# 💡 Driftskostnader (instant reset uten rerun)
# ===========================
# Init namespace første gang
# Init namespace
if "drift_ns" not in st.session_state:
    st.session_state["drift_ns"] = 0

# Reset-knapp FØR expanderen
if st.sidebar.button("Tilbakestill driftskostnader", key="btn_reset_drift"):
    st.session_state["drift_ns"] += 1

ns_drift = st.session_state["drift_ns"]
drift_title_total = sum_namespace("drift", driftskostnader_defaults, ns_drift)

with st.sidebar.expander(f"💡 Driftskostnader: {drift_title_total:,} kr", expanded=True):
    drift_total = 0
    for key, default in driftskostnader_defaults.items():
        wkey = f"drift_{key}_{ns_drift}"
        startverdi = st.session_state.get(wkey, 0 if ns_drift > 0 else default)
        val = st.number_input(key.capitalize(), value=startverdi, key=wkey, step=1000, format="%d")
        drift_total += val
    st.markdown(f"**Totalt: {int(drift_total):,} kr**")


# ------------------ Lån og finansiering ------------------
# Standardverdier i state kun første gang
lån_defaults = {
    "egenkapital": 300000,
    "rente": 5.0,
    "løpetid": 25,
    "avdragsfri": 2,
    "lånetype": "Annuitetslån",
    "eierform": "Privat",
}
for k, v in lån_defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Total investering nå
total_investering = kjøpesum + kjøpskostnader + oppussing_total
lånebeløp = max(total_investering - st.session_state["egenkapital"], 0)
st.session_state["lån"] = lånebeløp  # tilgjengelig for beregning

with st.sidebar.expander(f"🏦 Lån: {int(st.session_state['lån']):,} kr", expanded=True):
    st.session_state["egenkapital"] = st.number_input(
        "Egenkapital", value=st.session_state["egenkapital"], min_value=0, step=10000
    )
    # oppdater lånebeløp live
    st.session_state["lån"] = max(total_investering - st.session_state["egenkapital"], 0)

    st.session_state["rente"]     = st.number_input("Rente (%)", value=st.session_state["rente"], step=0.1)
    st.session_state["løpetid"]   = st.number_input("Løpetid (år)", value=st.session_state["løpetid"], step=1, min_value=1)
    st.session_state["avdragsfri"]= st.number_input("Avdragsfri (år)", value=st.session_state["avdragsfri"], step=1, min_value=0)
    st.session_state["lånetype"]  = st.selectbox("Lånetype", ["Annuitetslån", "Serielån"],
                                  index=["Annuitetslån", "Serielån"].index(st.session_state["lånetype"]))
    st.session_state["eierform"]  = st.radio("Eierform", ["Privat", "AS"],
                                  index=["Privat", "AS"].index(st.session_state["eierform"]))

# ------------------ Lånekalkyle ------------------
def beregn_lån(lån, rente, løpetid, avdragsfri, lånetype, leie, drift, eierform):
    n  = int(løpetid * 12)
    af = int(avdragsfri * 12)
    r  = rente / 100 / 12

    if lånetype == "Annuitetslån" and r > 0 and (n - af) > 0:
        terminbeløp = lån * (r * (1 + r)**(n - af)) / ((1 + r)**(n - af) - 1)
    else:
        terminbeløp = lån / (n - af) if (n - af) > 0 else 0

    saldo = lån
    restgjeld, avdrag, renter_liste, netto_cf, akk_cf = [], [], [], [], []
    akk = 0.0

    for m in range(n):
        rente_mnd = saldo * r
        if m < af:
            avdrag_mnd = 0.0
            termin = rente_mnd
        elif lånetype == "Serielån" and (n - af) > 0:
            avdrag_mnd = lån / (n - af)
            termin = avdrag_mnd + rente_mnd
        else:
            avdrag_mnd = terminbeløp - rente_mnd
            termin = terminbeløp

        saldo = max(saldo - avdrag_mnd, 0.0)
        netto = leie - (drift / 12.0) - termin
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

# ------------------ Beregning / Resultater ------------------
df, akk = beregn_lån(
    st.session_state["lån"],
    st.session_state["rente"],
    st.session_state["løpetid"],
    st.session_state["avdragsfri"],
    st.session_state["lånetype"],
    leie,
    drift_total,
    st.session_state["eierform"]
)

st.subheader("✨ Resultater")
st.metric("Total investering", f"{int(total_investering):,} kr")
st.metric("Brutto yield", f"{(leie * 12 / total_investering) * 100:.2f} %")
st.metric("Netto yield", f"{((leie * 12 - drift_total) / total_investering) * 100:.2f} %")

st.subheader("Kontantstrøm (første 60 måneder)")
st.dataframe(df.head(60), use_container_width=True, height=500)

st.subheader("Grafer")
st.line_chart(df[["Netto cashflow", "Akk. cashflow"]])
st.line_chart(df[["Renter", "Avdrag"]])
st.line_chart(df["Restgjeld"])
