
import streamlit as st

st.set_page_config(layout="wide")
st.markdown("""
    <style>
    ::-webkit-scrollbar {
        width: 12px;
    }
    ::-webkit-scrollbar-thumb {
        background-color: #888;
        border-radius: 6px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("AMO Eiendom v49.2.15 – Bedre lagring og scrollbar")

# Innlogging
if "access_granted" not in st.session_state:
    pwd = st.text_input("Passord", type="password")
    if pwd != "amo123":
        st.stop()
    st.session_state.access_granted = True
    st.rerun()

# Feltstruktur og nullstillingskategorier
felt_navn = {
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
    "finnlink": "",
    "eiendomsnavn": ""
}
nullstillingsfelter = {
    "grunnleggende": ["kjøpesum", "leie"],
    "oppussing": ["riving", "bad", "kjøkken", "overflate", "gulv", "rørlegger", "elektriker", "utvendig"],
    "drift": ["forsikring", "strøm", "kommunale", "internett", "vedlikehold"],
    "finans": ["lån", "rente", "løpetid", "avdragsfri"],
}
st.session_state.setdefault("nullstilt_felter", [])

# Init state
for k, v in felt_navn.items():
    st.session_state.setdefault(k, v)
st.session_state.setdefault("eiendommer", {})
st.session_state.setdefault("valgt_eiendom", "")
st.session_state.setdefault("lagret_sist", "")

# Nullstilling etter rerun
for f in st.session_state["nullstilt_felter"]:
    st.session_state[f] = 0.0
st.session_state["nullstilt_felter"] = []

# Funksjoner
def nullstill(kategori):
    st.session_state["nullstilt_felter"] = nullstillingsfelter[kategori]
    st.rerun()

def lagre_eiendom():
    navn = st.session_state["eiendomsnavn"].strip()
    if navn:
        st.session_state.eiendommer[navn] = {k: st.session_state[k] for k in felt_navn}
        st.session_state.valgt_eiendom = navn
        st.session_state.lagret_sist = navn
    else:
        st.warning("Du må skrive inn navn på eiendommen før du kan lagre.")

def last_eiendom(navn):
    data = st.session_state.eiendommer.get(navn)
    if data:
        for k, v in data.items():
            st.session_state[k] = v
        st.session_state["valgt_eiendom"] = navn
        st.rerun()

def slett_eiendom():
    navn = st.session_state["valgt_eiendom"]
    if navn and navn in st.session_state.eiendommer:
        del st.session_state.eiendommer[navn]
        st.session_state["valgt_eiendom"] = ""
        st.session_state.lagret_sist = ""
        st.rerun()

# Sidebar
with st.sidebar:
    st.text_input("Navn på eiendom", key="eiendomsnavn")
    st.text_input("Finn-annonselenke", key="finnlink")

    st.markdown("### Grunnleggende")
    st.number_input("Kjøpesum", value=float(st.session_state["kjøpesum"]), key="kjøpesum", step=100000.0, format="%.0f")
    st.number_input("Leie/mnd", value=float(st.session_state["leie"]), key="leie", step=1000.0, format="%.0f")
    st.button("Nullstill grunnleggende", on_click=nullstill, args=("grunnleggende",))

    st.markdown("### Oppussing")
    for felt in nullstillingsfelter["oppussing"]:
        st.number_input(felt.capitalize(), value=float(st.session_state[felt]), key=felt, step=10000.0, format="%.0f")
    st.button("Nullstill oppussing", on_click=nullstill, args=("oppussing",))

    st.markdown("### Driftskostnader")
    for felt in nullstillingsfelter["drift"]:
        st.number_input(felt.capitalize(), value=float(st.session_state[felt]), key=felt, step=1000.0, format="%.0f")
    st.button("Nullstill driftskostnader", on_click=nullstill, args=("drift",))

    st.markdown("### Lån og rente")
    st.number_input("Lån", value=float(st.session_state["lån"]), key="lån", step=100000.0, format="%.0f")
    st.number_input("Rente", value=float(st.session_state["rente"]), key="rente", step=0.1, format="%.2f")
    st.number_input("Løpetid", value=float(st.session_state["løpetid"]), key="løpetid", step=1.0, format="%.0f")
    st.number_input("Avdragsfri", value=float(st.session_state["avdragsfri"]), key="avdragsfri", step=1.0, format="%.0f")
    st.button("Nullstill finansiering", on_click=nullstill, args=("finans",))

    st.button("Lagre eiendom", on_click=lagre_eiendom)

    if st.session_state.eiendommer:
        valgt = st.selectbox("Velg eiendom", options=list(st.session_state.eiendommer.keys()), index=0 if not st.session_state["valgt_eiendom"] else list(st.session_state.eiendommer.keys()).index(st.session_state["valgt_eiendom"]))
        st.button("Last valgt eiendom", on_click=last_eiendom, args=(valgt,))
        st.button("Slett valgt eiendom", on_click=slett_eiendom)

# Hovedvisning
st.subheader("Aktiv eiendom")
st.markdown(f"**Navn:** {st.session_state.get('eiendomsnavn', '')}")
st.markdown(f"**Finn-link:** {st.session_state.get('finnlink', '')}")

if st.session_state.lagret_sist:
    st.success(f"Eiendom '{st.session_state.lagret_sist}' er lagret!")

st.subheader("Sammendrag")
for k in felt_navn:
    if k not in ["eiendomsnavn", "finnlink"]:
        st.write(f"{k}: {st.session_state.get(k)}")
