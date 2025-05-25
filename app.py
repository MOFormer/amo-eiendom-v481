
import streamlit as st

st.set_page_config(layout="wide")
st.title("AMO Eiendom v48.3.6 – Sidebar test")

st.success("Appen startet!")

try:
    with st.sidebar:
        st.header("Eiendomsdata")
        navn = st.text_input("Navn på eiendom", "Eksempelveien 1")
        kjøpesum = st.number_input("Kjøpesum", value=3000000.0, step=100000.0)
        oppussing = st.number_input("Oppussing", value=200000.0, step=10000.0)
        leie = st.number_input("Leieinntekter per måned", value=22000.0, step=1000.0)
        st.success("Sidebar lastet!")

    st.write(f"**Eiendom:** {navn}")
    st.write(f"Kjøpesum: {int(kjøpesum):,} kr")
    st.write(f"Oppussing: {int(oppussing):,} kr")
    st.write(f"Leieinntekter: {int(leie):,} kr/mnd")

except Exception as e:
    st.error(f"Feil under lasting av sidebar/input: {e}")
