
import streamlit as st

st.set_page_config(layout="wide")
st.title("AMO Eiendom v49.2.9 – MixedNumericTypesError løst")

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

# Init session state
for key, val in standardverdier.items():
    st.session_state.setdefault(key, val)

# Nullstill-funksjon
def nullstill(feltnavn):
    for f in feltnavn:
        st.session_state[f] = 0.0

# Inndata – bruker eksplisitt typecasting for å unngå feil
with st.sidebar:
    st.subheader("Grunnleggende")
    st.number_input("Kjøpesum", value=int(st.session_state["kjøpesum"]), key="kjøpesum", step=100000, format="%.0f")
    st.number_input("Leie/mnd", value=int(st.session_state["leie"]), key="leie", step=1000, format="%.0f")
    if st.button("Nullstill grunnleggende"):
        nullstill(["kjøpesum", "leie"])

    st.subheader("Oppussing")
    for felt in ["riving", "bad", "kjøkken", "overflate", "gulv", "rørlegger", "elektriker", "utvendig"]:
        st.number_input(felt.capitalize(), value=int(st.session_state[felt]), key=felt, step=10000, format="%.0f")
    if st.button("Nullstill oppussing"):
        nullstill(["riving", "bad", "kjøkken", "overflate", "gulv", "rørlegger", "elektriker", "utvendig"])

    st.subheader("Driftskostnader")
    for felt in ["forsikring", "strøm", "kommunale", "internett", "vedlikehold"]:
        st.number_input(felt.capitalize(), value=int(st.session_state[felt]), key=felt, step=1000, format="%.0f")
    if st.button("Nullstill driftskostnader"):
        nullstill(["forsikring", "strøm", "kommunale", "internett", "vedlikehold"])

    st.subheader("Lån og rente")
    st.number_input("Lån", value=int(st.session_state["lån"]), key="lån", step=100000, format="%.0f")
    st.number_input("Rente", value=float(st.session_state["rente"]), key="rente", step=0.1, format="%.2f")
    st.number_input("Løpetid", value=int(st.session_state["løpetid"]), key="løpetid", step=1, format="%.0f")
    st.number_input("Avdragsfri", value=int(st.session_state["avdragsfri"]), key="avdragsfri", step=1, format="%.0f")
    if st.button("Nullstill finansiering"):
        nullstill(["lån", "rente", "løpetid", "avdragsfri"])

# Vis resultat
st.subheader("Sammendrag av verdier")
for key in standardverdier:
    st.write(f"{key}: {st.session_state.get(key, 0)}")
