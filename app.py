
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("AMO Eiendom v48.5.4 – Umiddelbar visning og lagre-knapp")

# Passordbeskyttelse
if "access_granted" not in st.session_state:
    pwd = st.text_input("Skriv inn passord for tilgang", type="password")
    if pwd == "amo123":
        st.session_state.access_granted = True
        st.experimental_rerun()
    else:
        st.stop()

# Init eiendomsliste
if "eiendommer" not in st.session_state:
    st.session_state.eiendommer = {}

navn = st.sidebar.text_input("Navn på eiendom", "Eksempelveien 1")
finn_link = st.sidebar.text_input("Finn-lenke", "")
kjøpesum = st.sidebar.number_input("Kjøpesum", value=3000000.0, step=100000.0)

with st.sidebar.expander("Oppussing"):
    riving = st.number_input("Utrydding/riving", value=20000.0)
    bad = st.number_input("Bad", value=120000.0)
    kjøkken = st.number_input("Kjøkken", value=100000.0)
    overflate = st.number_input("Overflate", value=30000.0)
    gulv = st.number_input("Gulv/dører/lister", value=40000.0)
    rørlegger = st.number_input("Rørlegger", value=25000.0)
    elektriker = st.number_input("Elektriker", value=30000.0)
    utvendig = st.number_input("Utvendig", value=20000.0)
oppussing = sum([riving, bad, kjøkken, overflate, gulv, rørlegger, elektriker, utvendig])
st.sidebar.markdown(f"**Total oppussing:** {int(oppussing):,} kr")

leie = st.sidebar.number_input("Leieinntekter/mnd", value=22000.0)

with st.sidebar.expander("Driftskostnader per år"):
    forsikring = st.number_input("Forsikring", value=8000.0)
    strøm = st.number_input("Strøm", value=12000.0)
    kommunale = st.number_input("Kommunale avg./felleskost.", value=9000.0)
    internett = st.number_input("Internett", value=3000.0)
    vedlikehold = st.number_input("Vedlikehold", value=8000.0)
drift = sum([forsikring, strøm, kommunale, internett, vedlikehold])
st.sidebar.markdown(f"**Totale driftskostnader:** {int(drift):,} kr")

lån = st.sidebar.number_input("Lån", value=2700000.0)
rente = st.sidebar.number_input("Rente (%)", value=5.0)
løpetid = st.sidebar.number_input("Løpetid (år)", value=25)
avdragsfri = st.sidebar.number_input("Avdragsfri (år)", value=2)
lånetype = st.sidebar.selectbox("Lånetype", ["Annuitetslån", "Serielån"])
eierform = st.sidebar.radio("Eierform", ["Privat", "AS"])
vis_grafer = st.sidebar.checkbox("Vis grafer", value=True)

# Nedtrekk og lagre-knapp
st.sidebar.markdown("---")
if st.session_state.eiendommer:
    valgt = st.sidebar.selectbox("Velg eiendom", list(st.session_state.eiendommer.keys()))
    st.sidebar.markdown(f"**Valgt:** {valgt}")

if st.sidebar.button("Lagre endringer"):
    st.session_state.eiendommer[navn] = {
        "finn": finn_link, "kjøpesum": kjøpesum, "oppussing": oppussing,
        "leie": leie, "drift": drift, "lån": lån, "rente": rente,
        "løpetid": løpetid, "avdragsfri": avdragsfri, "lånetype": lånetype, "eierform": eierform
    }
    st.success(f"Lagret '{navn}'!")

# Beregning
total = kjøpesum + oppussing + kjøpesum * 0.025
n = int(løpetid * 12)
af = int(avdragsfri * 12)
r = rente / 100 / 12

if lånetype == "Annuitetslån" and r > 0:
    terminbeløp = lån * (r * (1 + r)**(n - af)) / ((1 + r)**(n - af) - 1)
else:
    terminbeløp = lån / (n - af) if (n - af) > 0 else 0

saldo = lån
restgjeld, avdrag, renter_liste, netto_cf, akk_cf = [], [], [], [], []
akk = 0

for m in range(n):
    rente_mnd = saldo * r
    if m < af:
        avdrag_mnd = 0
        termin = rente_mnd
    elif lånetype == "Serielån":
        avdrag_mnd = lån / (n - af)
        termin = avdrag_mnd + rente_mnd
    else:
        avdrag_mnd = terminbeløp - rente_mnd
        termin = terminbeløp

    saldo -= avdrag_mnd
    netto = leie - drift / 12 - termin
    if eierform == "AS" and netto > 0:
        netto -= netto * 0.375
    akk += netto

    restgjeld.append(saldo)
    avdrag.append(avdrag_mnd)
    renter_liste.append(rente_mnd)
    netto_cf.append(netto)
    akk_cf.append(akk)

# Resultatvisning
st.subheader(f"Resultater for: {navn}")
if finn_link:
    st.markdown(f"[Finn-annonse]({finn_link})", unsafe_allow_html=True)
st.metric("Total investering", f"{int(total):,} kr")
st.metric("Brutto yield", f"{(leie * 12 / total) * 100:.2f} %")
st.metric("Netto yield", f"{((leie * 12 - drift) / total) * 100:.2f} %")

df = pd.DataFrame({
    "Måned": list(range(1, n + 1)),
    "Restgjeld": restgjeld,
    "Avdrag": avdrag,
    "Renter": renter_liste,
    "Netto cashflow": netto_cf,
    "Akk. cashflow": akk_cf
})
st.dataframe(df.head(60))

if vis_grafer:
    st.line_chart(df[["Netto cashflow", "Akk. cashflow"]])
    st.line_chart(df[["Renter", "Avdrag"]])
    st.line_chart(df["Restgjeld"])
