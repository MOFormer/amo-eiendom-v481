
import streamlit as st

st.set_page_config(layout="wide")
st.title("AMO Eiendom v48.3.7 – Beregning & Yield")

st.success("Appen startet!")

try:
    with st.sidebar:
        st.header("Eiendomsdata")
        navn = st.text_input("Navn på eiendom", "Eksempelveien 1")
        kjøpesum = st.number_input("Kjøpesum", value=3000000.0, step=100000.0)
        oppussing = st.number_input("Oppussing", value=200000.0, step=10000.0)
        leie = st.number_input("Leieinntekter per måned", value=22000.0, step=1000.0)
        drift = st.number_input("Årlige driftskostnader", value=36000.0, step=1000.0)
        st.success("Sidebar lastet!")

    total_investering = kjøpesum + oppussing + kjøpesum * 0.025
    brutto_yield = (leie * 12) / total_investering * 100 if total_investering else 0
    netto_yield = ((leie * 12 - drift) / total_investering) * 100 if total_investering else 0

    st.subheader(f"Resultater for: {navn}")
    st.metric("Total investering", f"{int(total_investering):,} kr")
    st.metric("Brutto yield", f"{brutto_yield:.2f} %")
    st.metric("Netto yield", f"{netto_yield:.2f} %")

    st.success("Beregning OK!")

except Exception as e:
    st.error(f"Noe gikk galt i beregningen: {e}")
