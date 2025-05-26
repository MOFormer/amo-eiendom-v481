
import streamlit as st

st.set_page_config(layout="wide")
st.title("AMO Eiendom v49.2.11 – Nullstilling med flagg og trygg rerun")

# === Innlogging ===
if "access_granted" not in st.session_state:
    pwd = st.text_input("Passord", type="password")
    if pwd != "amo123":
        st.stop()
    st.session_state.access_granted = True
    st.rerun()

# === Standardverdier ===
standardverdier = {
    "kjøpesum": 3000000.0,
    "leie": 22000.0,
    "lån": 2700000.0,
    "rente": 5.0,
    "løpetid": 25,
    "avdragsfri": 2,
    "forsikring": 8000.0,
    "strøm": 12000.0,
    "kommunale": 9000.0,
    "internett": 3000.0,
    "vedlikehold": 8000.0,
    "riving": 20000.0,
    "bad": 120000.0,
    "kjøkken": 100000.0,
    "overflate": 30000.0,
    "gulv": 40000.0,
    "rørlegger": 25000.0,
    "elektriker": 30000.0,
    "utvendig": 20000.0,
}

# === Nullstillingsflagg ===
nullstillingsflagg = {
    "grunnleggende": "nullstill_grunnleggende",
    "oppussing": "nullstill_oppussing",
    "drift": "nullstill_drift",
    "finans": "nullstill_finans",
}

# === Nullstill tidlig hvis flagg er satt ===
for kategori, flagg in nullstillingsflagg.items():
    if st.session_state.get(flagg, False):
        felter = {
            "grunnleggende": ["kjøpesum", "leie"],
            "oppussing": ["riving", "bad", "kjøkken", "overflate", "gulv", "rørlegger", "elektriker", "utvendig"],
            "drift": ["forsikring", "strøm", "kommunale", "internett", "vedlikehold"],
            "finans": ["lån", "rente", "løpetid", "avdragsfri"],
        }[kategori]
        for f in felter:
            st.session_state[f] = 0.0
        st.session_state[flagg] = False
        st.rerun()

# === Init session state ===
for key, val in standardverdier.items():
    st.session_state.setdefault(key, val)

# === Inndata ===
with st.sidebar:
    st.subheader("Grunnleggende")
    st.number_input("Kjøpesum", value=float(st.session_state["kjøpesum"]), key="kjøpesum", step=100000.0, format="%.0f")
    st.number_input("Leie/mnd", value=float(st.session_state["leie"]), key="leie", step=1000.0, format="%.0f")
    if st.button("Nullstill grunnleggende"):
        st.session_state[nullstillingsflagg["grunnleggende"]] = True
        st.rerun()

    st.subheader("Oppussing")
    for felt in ["riving", "bad", "kjøkken", "overflate", "gulv", "rørlegger", "elektriker", "utvendig"]:
        st.number_input(felt.capitalize(), value=float(st.session_state[felt]), key=felt, step=10000.0, format="%.0f")
    if st.button("Nullstill oppussing"):
        st.session_state[nullstillingsflagg["oppussing"]] = True
        st.rerun()

    st.subheader("Driftskostnader")
    for felt in ["forsikring", "strøm", "kommunale", "internett", "vedlikehold"]:
        st.number_input(felt.capitalize(), value=float(st.session_state[felt]), key=felt, step=1000.0, format="%.0f")
    if st.button("Nullstill driftskostnader"):
        st.session_state[nullstillingsflagg["drift"]] = True
        st.rerun()

    st.subheader("Lån og rente")
    st.number_input("Lån", value=float(st.session_state["lån"]), key="lån", step=100000.0, format="%.0f")
    st.number_input("Rente", value=float(st.session_state["rente"]), key="rente", step=0.1, format="%.2f")
    st.number_input("Løpetid", value=float(st.session_state["løpetid"]), key="løpetid", step=1.0, format="%.0f")
    st.number_input("Avdragsfri", value=float(st.session_state["avdragsfri"]), key="avdragsfri", step=1.0, format="%.0f")
    if st.button("Nullstill finansiering"):
        st.session_state[nullstillingsflagg["finans"]] = True
        st.rerun()

# === Resultat ===
st.subheader("Sammendrag av verdier")
for key in standardverdier:
    st.write(f"{key}: {st.session_state.get(key, 0)}")
