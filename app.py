import streamlit as st
import pandas as pd

# ------------------ Layout og stil ------------------
st.set_page_config(layout="wide")

# ------------------ Tittel ------------------
st.title("Eiendomskalkulator")

# ===========================
# OPPUSSING (RERUN-FREE, ROBUST)
# ===========================

# 1) Standardverdier
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

# 2) Namespace/nonce for widget keys (så vi kan “remounte” widgets uten rerun)
if "opp_ns" not in st.session_state:
    st.session_state["opp_ns"] = 0

# 3) Reset-modus (skal reset gi 0-verdier i stedet for defaults?)
if "opp_zero_mode" not in st.session_state:
    st.session_state["opp_zero_mode"] = False

# 4) UI
oppussing_total = 0
with st.sidebar.expander("🔨 Oppussing", expanded=True):
    # Bygg en unik suffix så widget-keys blir nye når vi resetter
    ns = st.session_state["opp_ns"]
    for key, default in oppussing_defaults.items():
        widget_key = f"opp_{key}_{ns}"  # << unik per “runde”
        startverdi = 0 if st.session_state["opp_zero_mode"] else default
        val = st.number_input(
            label=key.capitalize(),
            value=startverdi,
            key=widget_key,
            step=1000,
            format="%d",
        )
        oppussing_total += val

    st.markdown(f"**Totalt: {int(oppussing_total):,} kr**")

    if st.button("Tilbakestill oppussing", key=f"btn_reset_opp_{ns}"):
        # Neste render: øk namespace (nye keys) og gå i zero-mode
        st.session_state["opp_ns"] += 1
        st.session_state["opp_zero_mode"] = True

# 5) Etter første reset-render, gå tilbake til defaults for senere endringer
# (dvs. nuller kun på selve reset-klikket)
if st.session_state.get("opp_zero_mode", False):
    # slå av etter at nye widgets er rendret én gang
    st.session_state["opp_zero_mode"] = False
# ===========================
# DRIFTSKOSTNADER (RERUN-FREE, ROBUST)
# ===========================

# 1) Standardverdier – MÅ stå før bruk
driftskostnader_defaults = {
    "forsikring": 8000,
    "strøm": 12000,
    "kommunale avgifter": 9000,
    "internett": 3000,
    "vedlikehold": 8000,
}

# 2) Namespace/nonce for widget keys (remounter widgets uten rerun)
if "drift_ns" not in st.session_state:
    st.session_state["drift_ns"] = 0

# 3) Reset-modus: om neste render skal starte på 0
if "drift_zero_mode" not in st.session_state:
    st.session_state["drift_zero_mode"] = False

# 4) UI
drift_total = 0
with st.sidebar.expander("📈 Driftskostnader", expanded=True):
    ns = st.session_state["drift_ns"]
    for key, default in driftskostnader_defaults.items():
        widget_key = f"drift_{key}_{ns}"  # unikt per runde
        startverdi = 0 if st.session_state["drift_zero_mode"] else default
        val = st.number_input(
            label=key.capitalize(),
            value=startverdi,
            key=widget_key,
            step=1000,
            format="%d",
        )
        drift_total += val

    st.markdown(f"**Totalt: {int(drift_total):,} kr**")

    if st.button("Tilbakestill driftskostnader", key=f"btn_reset_drift_{ns}"):
        st.session_state["drift_ns"] += 1
        st.session_state["drift_zero_mode"] = True

# 5) Slå av zero-mode etter første reset-render
if st.session_state.get("drift_zero_mode", False):
    st.session_state["drift_zero_mode"] = False
