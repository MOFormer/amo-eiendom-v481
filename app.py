
import streamlit as st

st.set_page_config(layout="wide")
st.title("AMO Eiendom v49.2.3 – Nullstill som faktisk nullstiller!")

# Innlogging
if "access_granted" not in st.session_state:
    pwd = st.text_input("Passord", type="password")
    if pwd != "amo123":
        st.stop()
    st.session_state.access_granted = True
    st.rerun()

# Standardverdier
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

# Nullstill-funksjon
def nullstill(feltnavn):
    for f in feltnavn:
        if f in st.session_state:
            st.session_state[f] = 0.0
    st.rerun()

# INPUT med eksplisitt håndtering
with st.sidebar:
    st.subheader("Grunnleggende")
    kjøpesum = st.number_input("Kjøpesum", value=st.session_state.get("kjøpesum", 0.0), step=100000.0, format="%.0f")
    leie = st.number_input("Leie/mnd", value=st.session_state.get("leie", 0.0), step=1000.0, format="%.0f")
    st.session_state["kjøpesum"] = kjøpesum
    st.session_state["leie"] = leie
    if st.button("Nullstill grunnleggende"):
        nullstill(["kjøpesum", "leie"])

    st.subheader("Oppussing")
    for felt in ["riving", "bad", "kjøkken", "overflate", "gulv", "rørlegger", "elektriker", "utvendig"]:
        val = st.number_input(felt.capitalize(), value=st.session_state.get(felt, 0.0))
        st.session_state[felt] = val
    if st.button("Nullstill oppussing"):
        nullstill(["riving", "bad", "kjøkken", "overflate", "gulv", "rørlegger", "elektriker", "utvendig"])

    st.subheader("Driftskostnader")
    for felt in ["forsikring", "strøm", "kommunale", "internett", "vedlikehold"]:
        val = st.number_input(felt.capitalize(), value=st.session_state.get(felt, 0.0))
        st.session_state[felt] = val
    if st.button("Nullstill driftskostnader"):
        nullstill(["forsikring", "strøm", "kommunale", "internett", "vedlikehold"])

    st.subheader("Lån og rente")
    for felt in ["lån", "rente", "løpetid", "avdragsfri"]:
        val = st.number_input(felt.capitalize(), value=st.session_state.get(felt, 0.0))
        st.session_state[felt] = val
    if st.button("Nullstill finansiering"):
        nullstill(["lån", "rente", "løpetid", "avdragsfri"])

# Sammendrag
st.subheader("Sammendrag (verdier etter justering)")
for k in standardverdier:
    st.write(f"{k}: {st.session_state.get(k, 0)}")
