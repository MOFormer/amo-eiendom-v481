
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("AMO Eiendom v48.5.6 – Lagre og slett fungerer riktig")

# Passordbeskyttelse
if "access_granted" not in st.session_state:
    pwd = st.text_input("Skriv inn passord for tilgang", type="password")
    if pwd == "amo123":
        st.session_state.access_granted = True
        st.experimental_rerun()
    else:
        st.stop()

if "eiendommer" not in st.session_state:
    st.session_state.eiendommer = {}

# Hent valgt eiendom
valg_liste = ["(Ny eiendom)"] + list(st.session_state.eiendommer.keys())
valgt_navn = st.sidebar.selectbox("Velg eiendom", valg_liste)
er_ny = valgt_navn == "(Ny eiendom)"
data = st.session_state.eiendommer.get(valgt_navn, {}) if not er_ny else {}

# Inndata
navn = st.sidebar.text_input("Navn på eiendom", value=valgt_navn if not er_ny else "")
finn_link = st.sidebar.text_input("Finn-lenke", value=data.get("finn", ""))
kjøpesum = st.sidebar.number_input("Kjøpesum", value=data.get("kjøpesum", 3000000.0), step=100000.0)

with st.sidebar.expander("Oppussing"):
    riving = st.number_input("Utrydding/riving", value=data.get("riving", 20000.0))
    bad = st.number_input("Bad", value=data.get("bad", 120000.0))
    kjøkken = st.number_input("Kjøkken", value=data.get("kjøkken", 100000.0))
    overflate = st.number_input("Overflate", value=data.get("overflate", 30000.0))
    gulv = st.number_input("Gulv/dører/lister", value=data.get("gulv", 40000.0))
    rørlegger = st.number_input("Rørlegger", value=data.get("rørlegger", 25000.0))
    elektriker = st.number_input("Elektriker", value=data.get("elektriker", 30000.0))
    utvendig = st.number_input("Utvendig", value=data.get("utvendig", 20000.0))
oppussing = sum([riving, bad, kjøkken, overflate, gulv, rørlegger, elektriker, utvendig])
st.sidebar.markdown(f"**Total oppussing:** {int(oppussing):,} kr")

leie = st.sidebar.number_input("Leieinntekter/mnd", value=data.get("leie", 22000.0))

with st.sidebar.expander("Driftskostnader per år"):
    forsikring = st.number_input("Forsikring", value=data.get("forsikring", 8000.0))
    strøm = st.number_input("Strøm", value=data.get("strøm", 12000.0))
    kommunale = st.number_input("Kommunale avg./felleskost.", value=data.get("kommunale", 9000.0))
    internett = st.number_input("Internett", value=data.get("internett", 3000.0))
    vedlikehold = st.number_input("Vedlikehold", value=data.get("vedlikehold", 8000.0))
drift = sum([forsikring, strøm, kommunale, internett, vedlikehold])
st.sidebar.markdown(f"**Totale driftskostnader:** {int(drift):,} kr")

lån = st.sidebar.number_input("Lån", value=data.get("lån", 2700000.0))
rente = st.sidebar.number_input("Rente (%)", value=data.get("rente", 5.0))
løpetid = st.sidebar.number_input("Løpetid (år)", value=data.get("løpetid", 25))
avdragsfri = st.sidebar.number_input("Avdragsfri (år)", value=data.get("avdragsfri", 2))
lånetype = st.sidebar.selectbox("Lånetype", ["Annuitetslån", "Serielån"], index=["Annuitetslån", "Serielån"].index(data.get("lånetype", "Annuitetslån")))
eierform = st.sidebar.radio("Eierform", ["Privat", "AS"], index=["Privat", "AS"].index(data.get("eierform", "Privat")))
vis_grafer = st.sidebar.checkbox("Vis grafer", value=True)

# Lagre og slett
if st.sidebar.button("Lagre endringer"):
    st.session_state.eiendommer[navn] = {
        "finn": finn_link, "kjøpesum": kjøpesum, "leie": leie,
        "lån": lån, "rente": rente, "løpetid": løpetid, "avdragsfri": avdragsfri,
        "lånetype": lånetype, "eierform": eierform,
        "riving": riving, "bad": bad, "kjøkken": kjøkken, "overflate": overflate,
        "gulv": gulv, "rørlegger": rørlegger, "elektriker": elektriker, "utvendig": utvendig,
        "forsikring": forsikring, "strøm": strøm, "kommunale": kommunale,
        "internett": internett, "vedlikehold": vedlikehold
    }
    st.success(f"Eiendom '{navn}' lagret.")
    st.experimental_rerun()

if not er_ny:
    if st.sidebar.button("Slett eiendom"):
        st.session_state.eiendommer.pop(valgt_navn, None)
        st.success(f"Slettet '{valgt_navn}'.")
        st.experimental_rerun()

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

# Vis resultater
st.subheader(f"Resultater for: {navn}")
if finn_link:
    st.markdown(f"[Se Finn-annonse]({finn_link})", unsafe_allow_html=True)
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
