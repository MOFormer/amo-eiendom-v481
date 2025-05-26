
import streamlit as st

st.set_page_config(layout="wide")
st.title("AMO Eiendom v49.2.1 – Nullstill uten feil")

# Innlogging
if "access_granted" not in st.session_state:
    pwd = st.text_input("Passord", type="password")
    if pwd != "amo123":
        st.stop()
    st.session_state.access_granted = True
    st.rerun()

# Init
feltgrupper = {
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
for key, val in feltgrupper.items():
    if key not in st.session_state:
        st.session_state[key] = val

# Trygg nullstilling
def nullstill(feltnavn):
    for f in feltnavn:
        if f in st.session_state:
            del st.session_state[f]
    st.rerun()

# Inndata med trygge nullstillinger
with st.sidebar:
    st.subheader("Grunnleggende")
    st.number_input("Kjøpesum", key="kjøpesum", step=100000.0, format="%.0f")
    st.number_input("Leie/mnd", key="leie", step=1000.0, format="%.0f")
    if st.button("Nullstill grunnleggende"):
        nullstill(["kjøpesum", "leie"])

    st.subheader("Oppussing")
    st.number_input("Utrydding/riving", key="riving")
    st.number_input("Bad", key="bad")
    st.number_input("Kjøkken", key="kjøkken")
    st.number_input("Overflate", key="overflate")
    st.number_input("Gulv/dører/lister", key="gulv")
    st.number_input("Rørlegger", key="rørlegger")
    st.number_input("Elektriker", key="elektriker")
    st.number_input("Utvendig", key="utvendig")
    if st.button("Nullstill oppussing"):
        nullstill(["riving", "bad", "kjøkken", "overflate", "gulv", "rørlegger", "elektriker", "utvendig"])

    st.subheader("Driftskostnader")
    st.number_input("Forsikring", key="forsikring")
    st.number_input("Strøm", key="strøm")
    st.number_input("Kommunale avgifter", key="kommunale")
    st.number_input("Internett", key="internett")
    st.number_input("Vedlikehold", key="vedlikehold")
    if st.button("Nullstill driftskostnader"):
        nullstill(["forsikring", "strøm", "kommunale", "internett", "vedlikehold"])

    st.subheader("Lån og rente")
    st.number_input("Lånebeløp", key="lån", step=100000.0, format="%.0f")
    st.number_input("Rente (%)", key="rente")
    st.number_input("Løpetid (år)", key="løpetid")
    st.number_input("Avdragsfri (år)", key="avdragsfri")
    if st.button("Nullstill finansiering"):
        nullstill(["lån", "rente", "løpetid", "avdragsfri"])

# Vis sammendrag
st.subheader("Sammendrag (test)")
for key in feltgrupper:
    st.write(f"{key}: {st.session_state[key]}")
