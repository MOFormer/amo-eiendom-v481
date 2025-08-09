import streamlit as st
import pandas as pd

# ------------------ Layout og stil ------------------
st.set_page_config(layout="wide")

# ------------------ Tittel ------------------
st.title("Eiendomskalkulator")

# ------------------ Standardverdier ------------------
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

# --- Reset-trigger for Oppussing (må være før UI) ---
if "reset_oppussing_triggered" not in st.session_state:
    st.session_state["reset_oppussing_triggered"] = False

# --- Utfør reset tidlig og rerun trygt ---
if st.session_state["reset_oppussing_triggered"]:
    for _key in oppussing_defaults:
        k = f"opp_{_key}"
        if k in st.session_state:
            del st.session_state[k]
    st.session_state["reset_oppussing_triggered"] = False
    st.experimental_rerun()

driftskostnader_defaults = {
    "forsikring": 8000,
    "strøm": 12000,
    "kommunale avgifter": 9000,
    "internett": 3000,
    "vedlikehold": 8000,
}

# ------------------ Init reset-triggere ------------------
if "reset_oppussing_triggered" not in st.session_state:
    st.session_state["reset_oppussing_triggered"] = False

if "reset_drift_triggered" not in st.session_state:
    st.session_state["reset_drift_triggered"] = False

# ------------------ Oppussing reset ------------------
for key, default in oppussing_defaults.items():
    widget_key = f"opp_{key}"
    if widget_key not in st.session_state or st.session_state["reset_oppussing_triggered"]:
        st.session_state[widget_key] = 0 if st.session_state["reset_oppussing_triggered"] else default
if st.session_state["reset_oppussing_triggered"]:
    st.session_state["reset_oppussing_triggered"] = False

# ------------------ Driftskostnader reset ------------------
for key, default in driftskostnader_defaults.items():
    widget_key = f"drift_{key}"
    if widget_key not in st.session_state or st.session_state["reset_drift_triggered"]:
        st.session_state[widget_key] = 0 if st.session_state["reset_drift_triggered"] else default
if st.session_state["reset_drift_triggered"]:
    st.session_state["reset_drift_triggered"] = False

# ------------------ Sidebar: Kjøp og oppussing ------------------
st.sidebar.header("🧾 Kjøp og oppussing")

# Kjøpesum
kjøpesum = st.sidebar.number_input("Kjøpesum", value=4_000_000, step=100_000)
kjøpskostnader = kjøpesum * 0.025

# Oppussing
oppussing_total = 0
if st.button("Tilbakestill oppussing", key="reset_oppussing_btn"):
    st.session_state["reset_oppussing_triggered"] = True
    for key in oppussing_defaults:
        widget_key = f"opp_{key}"
        val = st.number_input(
            label=key.capitalize(),
            value=st.session_state[widget_key],
            key=widget_key,
            step=1000,
            format="%d"
        )
        oppussing_total += val
    st.markdown(f"**Totalt: {int(oppussing_total):,} kr**")
    if st.button("Tilbakestill oppussing", key="reset_oppussing_btn"):
        st.session_state["reset_oppussing_triggered"] = True
        st.experimental_rerun()

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
