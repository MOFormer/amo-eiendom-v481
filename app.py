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
# Driftskostnader
drift_total = 0
with st.sidebar.expander("💡 Driftskostnader", expanded=True):
    for key in driftskostnader_defaults:
        widget_key = f"drift_{key}"
        val = st.number_input(
            label=key.capitalize(),
            value=st.session_state[widget_key],
            key=widget_key,
            step=1000,
            format="%d"
        )
        drift_total += val
    st.markdown(f"**Totalt: {int(drift_total):,} kr**")
    if st.button("Tilbakestill driftskostnader", key="reset_drift_btn"):
        st.session_state["reset_drift_triggered"] = True
        st.experimental_rerun()

# Leie
leie = st.sidebar.number_input("Leieinntekter / mnd", value=22000)

# ------------------ Kalkulasjoner ------------------
total_investering = kjøpesum + kjøpskostnader + oppussing_total

st.subheader("✨ Resultater")
st.metric("Total investering", f"{int(total_investering):,} kr")
st.metric("Brutto yield", f"{(leie * 12 / total_investering) * 100:.2f} %")
st.metric("Netto yield", f"{((leie * 12 - drift_total) / total_investering) * 100:.2f} %")
