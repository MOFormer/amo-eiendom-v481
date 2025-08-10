import streamlit as st
import pandas as pd
import json
from pathlib import Path

# ---------- PERSIST / AUTOSAVE (MÅ KOMME FØR NOE ANNEN KODE) ----------
PERSIST_PATH = Path("autosave.json")

def _load_persist() -> dict:
    if PERSIST_PATH.exists():
        try:
            return json.loads(PERSIST_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def _save_persist(data: dict):
    try:
        PERSIST_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

# init session_state nøkler før bruk
if "persist" not in st.session_state:
    st.session_state["persist"] = _load_persist()
if "_dirty" not in st.session_state:
    st.session_state["_dirty"] = False

def mark_dirty():
    st.session_state["_dirty"] = True
# ----------------------------------------------------------------------

# ===========================
# Layout & stil
# ===========================
st.set_page_config(layout="wide")
st.markdown("""
    <style>
    div[data-testid="stDataFrameScrollable"]::-webkit-scrollbar { width: 16px; }
    div[data-testid="stDataFrameScrollable"]::-webkit-scrollbar-thumb { background-color: #444; border-radius: 8px; }
    div[data-testid="stDataFrameScrollable"]::-webkit-scrollbar-thumb:hover { background-color: #222; }
    </style>
""", unsafe_allow_html=True)

st.title("Eiendomskalkulator – med synlig scrollbar")

# ===========================
# Sidebar: Eiendomsinfo
# ===========================
st.sidebar.header("🧾 Eiendomsinfo")
kjøpesum_default = st.session_state["persist"].get("kjøpesum", 4_000_000)
leie_default     = st.session_state["persist"].get("leie", 22_000)

kjøpesum = st.sidebar.number_input(
    "Kjøpesum", value=int(kjøpesum_default), step=100_000, key="kjøpesum_input", on_change=mark_dirty
)
leie = st.sidebar.number_input(
    "Leieinntekter / mnd", value=int(leie_default), step=1_000, key="leie_input", on_change=mark_dirty
)

# speil til persist
st.session_state["persist"]["kjøpesum"] = int(kjøpesum)
st.session_state["persist"]["leie"] = int(leie)

Dokumentavgift = int(kjøpesum * 0.025)  # 2.5 % kjøpsomkostninger

# ===========================
# Defaults
# ===========================
oppussing_defaults = {
    "riving": 20000, "bad": 120000, "kjøkken": 100000, "overflate": 30000,
    "gulv": 40000, "rørlegger": 25000, "elektriker": 30000, "utvendig": 20000,
}
driftskostnader_defaults = {
    "forsikring": 8000, "strøm": 12000, "kommunale avgifter": 9000,
    "internett": 3000, "vedlikehold": 8000,
}

# ===========================
# Felles util
# ===========================
def sum_namespace(prefix: str, defaults: dict, ns: int) -> int:
    total = 0
    for key in defaults:
        total += int(st.session_state.get(f"{prefix}_{key}_{ns}", 0) or 0)
    return total

# Ekspander-styring
def expand_section(section: str):
    st.session_state[f"{section}_expanded"] = True
def reset_and_expand(section: str, reset_flag: str):
    st.session_state[reset_flag] = True
    st.session_state[f"{section}_expanded"] = True

for _flag in ("opp_expanded", "drift_expanded"):
    if _flag not in st.session_state:
        st.session_state[_flag] = False

# ===========================
# Pre-reset namespace-flagg
# ===========================
if "opp_ns" not in st.session_state:
    st.session_state["opp_ns"] = 0
if "opp_reset_request" not in st.session_state:
    st.session_state["opp_reset_request"] = False
if st.session_state["opp_reset_request"]:
    st.session_state["opp_ns"] += 1
    st.session_state["opp_reset_request"] = False

if "drift_ns" not in st.session_state:
    st.session_state["drift_ns"] = 0
if "drift_reset_request" not in st.session_state:
    st.session_state["drift_reset_request"] = False
if st.session_state["drift_reset_request"]:
    st.session_state["drift_ns"] += 1
    st.session_state["drift_reset_request"] = False

# ===========================
# Oppussing
# ===========================
st.session_state["persist"].setdefault("opp", {})
opp_title_total = sum_namespace("opp", oppussing_defaults, st.session_state["opp_ns"])

with st.sidebar.expander("🔨 Oppussing", expanded=st.session_state["opp_expanded"]):
    st.caption(f"**Sum oppussing:** {opp_title_total:,} kr")
    st.button("Tilbakestill oppussing", key="btn_reset_opp",
              on_click=reset_and_expand, args=("opp", "opp_reset_request"))

    ns = st.session_state["opp_ns"]
    oppussing_total = 0
    for key, default in oppussing_defaults.items():
        logic_key = key
        saved_val = st.session_state["persist"]["opp"].get(logic_key, default if ns == 0 else 0)
        wkey = f"opp_{key}_{ns}"
        val = st.number_input(
            key.capitalize(),
            value=int(st.session_state.get(wkey, saved_val)),
            key=wkey, step=1000, format="%d",
            on_change=expand_section, args=("opp",),
        )
        oppussing_total += int(val)
        if st.session_state["persist"]["opp"].get(logic_key) != int(val):
            st.session_state["persist"]["opp"][logic_key] = int(val)
            mark_dirty()
    st.markdown(f"**Totalt: {int(oppussing_total):,} kr**")

# ===========================
# Driftskostnader
# ===========================
st.session_state["persist"].setdefault("drift", {})
drift_title_total = sum_namespace("drift", driftskostnader_defaults, st.session_state["drift_ns"])

with st.sidebar.expander("💡 Driftskostnader", expanded=st.session_state["drift_expanded"]):
    st.caption(f"**Sum driftskostnader:** {drift_title_total:,} kr")
    st.button("Tilbakestill driftskostnader", key="btn_reset_drift",
              on_click=reset_and_expand, args=("drift", "drift_reset_request"))

    ns = st.session_state["drift_ns"]
    drift_total = 0
    for key, default in driftskostnader_defaults.items():
        logic_key = key
        saved_val = st.session_state["persist"]["drift"].get(logic_key, default if ns == 0 else 0)
        wkey = f"drift_{key}_{ns}"
        val = st.number_input(
            key.capitalize(),
            value=int(st.session_state.get(wkey, saved_val)),
            key=wkey, step=1000, format="%d",
            on_change=expand_section, args=("drift",),
        )
        drift_total += int(val)
        if st.session_state["persist"]["drift"].get(logic_key) != int(val):
            st.session_state["persist"]["drift"][logic_key] = int(val)
            mark_dirty()
    st.markdown(f"**Totalt: {int(drift_total):,} kr**")

# ===========================
# Lån og finansiering
# ===========================
lån_defaults = {
    "egenkapital": 300000, "rente": 5.0, "løpetid": 25,
    "avdragsfri": 2, "lånetype": "Annuitetslån", "eierform": "Privat",
}
for k, v in lån_defaults.items():
    if k not in st.session_state:
        st.session_state[k] = st.session_state["persist"].get(k, v)

total_investering = int(kjøpesum + Dokumentavgift + oppussing_total)
lånebeløp = max(total_investering - int(st.session_state["egenkapital"]), 0)
st.session_state["lån"] = lånebeløp

with st.sidebar.expander(f"🏦 Lån: {int(st.session_state['lån']):,} kr", expanded=False):
    st.session_state["egenkapital"] = st.number_input(
        "Egenkapital", value=int(st.session_state["egenkapital"]), min_value=0, step=10000, on_change=mark_dirty
    )
    st.session_state["lån"] = max(total_investering - int(st.session_state["egenkapital"]), 0)
    st.session_state["rente"]     = st.number_input("Rente (%)", value=float(st.session_state["rente"]), step=0.1, on_change=mark_dirty)
    st.session_state["løpetid"]   = st.number_input("Løpetid (år)", value=int(st.session_state["løpetid"]), step=1, min_value=1, on_change=mark_dirty)
    st.session_state["avdragsfri"]= st.number_input("Avdragsfri (år)", value=int(st.session_state["avdragsfri"]), step=1, min_value=0, on_change=mark_dirty)
    st.session_state["lånetype"]  = st.selectbox("Lånetype", ["Annuitetslån", "Serielån"],
                                  index=["Annuitetslån", "Serielån"].index(st.session_state["lånetype"]))
    st.session_state["eierform"]  = st.radio("Eierform", ["Privat", "AS"],
                                  index=["Privat", "AS"].index(st.session_state["eierform"]))
# speil lån til persist
for k in ("egenkapital","rente","løpetid","avdragsfri","lånetype","eierform"):
    st.session_state["persist"][k] = st.session_state[k]
mark_dirty()

# ===========================
# Lånekalkyle
# ===========================
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

df, akk = beregn_lån(
    st.session_state["lån"],
    float(st.session_state["rente"]),
    int(st.session_state["løpetid"]),
    int(st.session_state["avdragsfri"]),
    st.session_state["lånetype"],
    int(leie),
    int(drift_total),
    st.session_state["eierform"],
)

# ===========================
# Resultater og grafer
# ===========================
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

# ===========================
# Autosave til slutt
# ===========================
if st.session_state.get("_dirty"):
    _save_persist(st.session_state["persist"])
    st.session_state["_dirty"] = False
