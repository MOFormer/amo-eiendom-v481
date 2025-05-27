
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

st.title("AMO Eiendom v49.2.17 – Raskt eiendomsvalg og sletting")

# Innlogging
if "access_granted" not in st.session_state:
    pwd = st.text_input("Passord", type="password")
    if pwd != "amo123":
        st.stop()
    st.session_state.access_granted = True
    st.rerun()

# Feltstruktur og init
felt_navn = {
    "kjøpesum": 0.0, "leie": 0.0, "lån": 0.0, "rente": 0.0, "løpetid": 0.0, "avdragsfri": 0.0,
    "forsikring": 0.0, "strøm": 0.0, "kommunale": 0.0, "internett": 0.0, "vedlikehold": 0.0,
    "riving": 0.0, "bad": 0.0, "kjøkken": 0.0, "overflate": 0.0, "gulv": 0.0,
    "rørlegger": 0.0, "elektriker": 0.0, "utvendig": 0.0,
    "finnlink": "", "eiendomsnavn": ""
}
for k, v in felt_navn.items():
    st.session_state.setdefault(k, v)
st.session_state.setdefault("eiendommer", {})
st.session_state.setdefault("valgt_eiendom", "")
st.session_state.setdefault("ny_klikket", False)

# === Funksjoner ===
def lagre_aktiv_eiendom():
    navn = st.session_state["eiendomsnavn"].strip()
    if navn:
        st.session_state.eiendommer[navn] = {k: st.session_state[k] for k in felt_navn}
        st.session_state["valgt_eiendom"] = navn

def nullstill_alle():
    for k, v in felt_navn.items():
        st.session_state[k] = "" if isinstance(v, str) else 0.0
    st.session_state["valgt_eiendom"] = ""
    st.session_state["ny_klikket"] = False
    st.rerun()

def ny_eiendom():
    lagre_aktiv_eiendom()
    st.session_state["ny_klikket"] = True

def last_eiendom(navn):
    if navn in st.session_state.eiendommer:
        for k, v in st.session_state.eiendommer[navn].items():
            st.session_state[k] = v
        st.session_state["valgt_eiendom"] = navn
        st.rerun()

def slett_eiendom():
    navn = st.session_state["valgt_eiendom"]
    if navn in st.session_state.eiendommer:
        del st.session_state.eiendommer[navn]
        st.session_state["valgt_eiendom"] = ""
        st.rerun()

# Automatisk lagring
lagre_aktiv_eiendom()
if st.session_state["ny_klikket"]:
    nullstill_alle()

# === SIDEBAR ===
with st.sidebar:
    st.markdown("## Velg eiendom")
    if st.session_state.eiendommer:
        valgt = st.selectbox("Eiendommer", list(st.session_state.eiendommer.keys()), key="valgt_eiendom_drop")
        st.button("Last valgt eiendom", on_click=last_eiendom, args=(valgt,))
        st.button("Slett valgt eiendom", on_click=slett_eiendom)

    st.markdown("---")
    st.markdown("## Ny / Rediger eiendom")
    st.text_input("Navn på eiendom", key="eiendomsnavn")
    st.text_input("Finn-annonselenke", key="finnlink")
    st.button("Ny eiendom", on_click=ny_eiendom)

    st.markdown("### Grunnleggende")
    st.number_input("Kjøpesum", key="kjøpesum", step=100000.0, format="%.0f")
    st.number_input("Leie/mnd", key="leie", step=1000.0, format="%.0f")

    st.markdown("### Oppussing")
    for felt in ["riving", "bad", "kjøkken", "overflate", "gulv", "rørlegger", "elektriker", "utvendig"]:
        st.number_input(felt.capitalize(), key=felt, step=10000.0, format="%.0f")

    st.markdown("### Driftskostnader")
    for felt in ["forsikring", "strøm", "kommunale", "internett", "vedlikehold"]:
        st.number_input(felt.capitalize(), key=felt, step=1000.0, format="%.0f")

    st.markdown("### Lån og rente")
    st.number_input("Lån", key="lån", step=100000.0, format="%.0f")
    st.number_input("Rente", key="rente", step=0.1, format="%.2f")
    st.number_input("Løpetid", key="løpetid", step=1.0, format="%.0f")
    st.number_input("Avdragsfri", key="avdragsfri", step=1.0, format="%.0f")

# === HOVEDVISNING ===
st.subheader("Aktiv eiendom")
st.markdown(f"**Navn:** {st.session_state.get('eiendomsnavn', '')}")
st.markdown(f"**Finn-link:** {st.session_state.get('finnlink', '')}")

st.subheader("Sammendrag")
for k in felt_navn:
    if k not in ["eiendomsnavn", "finnlink"]:
        st.write(f"{k}: {st.session_state[k]}")
