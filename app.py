import streamlit as st
import pandas as pd

# ------------------ Layout og stil ------------------
st.set_page_config(layout="wide")

# ------------------ Tittel ------------------
st.title("Eiendomskalkulator")

# ===========================
# OPPUSSING – DEL 1 (PLASSER DENNE HØYT I FILEN, FØR UI)
# ===========================

# Standardverdier for oppussing
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

# Init styringsflagg
if "opp_reset_mode" not in st.session_state:
    st.session_state["opp_reset_mode"] = False
if "opp_use_zero_defaults" not in st.session_state:
    st.session_state["opp_use_zero_defaults"] = False

# Håndter reset tidlig (før UI)
if st.session_state["opp_reset_mode"]:
    # Fjern eksisterende widget-nøkler slik at de kan få nye startverdier
    for _k in oppussing_defaults:
        kk = f"opp_{_k}"
        if kk in st.session_state:
            del st.session_state[kk]
    # Neste init-runde skal bruke nuller
    st.session_state["opp_use_zero_defaults"] = True
    st.session_state["opp_reset_mode"] = False
    st.experimental_rerun()

# Init første-verdier (eller nuller etter reset)
for _k, _default in oppussing_defaults.items():
    kk = f"opp_{_k}"
    if kk not in st.session_state:
        st.session_state[kk] = 0 if st.session_state["opp_use_zero_defaults"] else _default

# Slå av null-modus etter at den er brukt én gang
if st.session_state["opp_use_zero_defaults"]:
    st.session_state["opp_use_zero_defaults"] = False

# ===========================
# OPPUSSING – DEL 2 (UI I SIDEBAR DER DU ØNSKER)
# ===========================
oppussing_total = 0
with st.sidebar.expander("🔨 Oppussing", expanded=True):
    for key in oppussing_defaults:
        widget_key = f"opp_{key}"
        val = st.number_input(
            label=key.capitalize(),
            value=st.session_state[widget_key],
            key=widget_key,
            step=1000,
            format="%d",
        )
        oppussing_total += val

    st.markdown(f"**Totalt: {int(oppussing_total):,} kr**")

    # Kun sett trigger – selve resetten skjer helt øverst før UI
    if st.button("Tilbakestill oppussing", key="btn_reset_oppussing"):
        st.session_state["opp_reset_mode"] = True

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
