import streamlit as st
import pandas as pd
import json
from pathlib import Path
import base64
from io import BytesIO
import matplotlib.pyplot as plt

# ---------- PERSIST / AUTOSAVE ----------
PERSIST_PATH = Path("autosave.json")

def _load_persist() -> dict:
    if PERSIST_PATH.exists():
        try:
            return json.loads(PERSIST_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def _save_persist(data: dict):
    try:
        PERSIST_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

if "persist" not in st.session_state:
    st.session_state["persist"] = _load_persist()
if "_dirty" not in st.session_state:
    st.session_state["_dirty"] = False

def mark_dirty():
    st.session_state["_dirty"] = True
# ----------------------------------------

st.set_page_config(layout="wide")
st.title("AMO Eiendomskalkulator")

# ---------- Sidebar: Grunninfo ----------
st.sidebar.header("🧾 Eiendomsinfo")

proj_navn = st.sidebar.text_input(
    "Prosjektnavn",
    value=st.session_state["persist"].get("prosjekt_navn", "Eiendomsprosjekt"),
    on_change=mark_dirty,
)
finn_url = st.sidebar.text_input(
    "Finn-annonse (URL)",
    value=st.session_state["persist"].get("finn_url", ""),
    on_change=mark_dirty,
    placeholder="https://www.finn.no/realestate/..."
)
if finn_url and not finn_url.startswith(("http://", "https://")):
    finn_url = "https://" + finn_url

st.session_state["persist"]["prosjekt_navn"] = proj_navn
st.session_state["persist"]["finn_url"] = finn_url

kjøpesum = st.sidebar.number_input(
    "Kjøpesum",
    value=int(st.session_state["persist"].get("kjøpesum", 4_000_000)),
    step=100_000,
    on_change=mark_dirty,
)
leie = st.sidebar.number_input(
    "Leieinntekter / mnd",
    value=int(st.session_state["persist"].get("leie", 22_000)),
    step=1_000,
    on_change=mark_dirty,
)

st.session_state["persist"]["kjøpesum"] = int(kjøpesum)
st.session_state["persist"]["leie"] = int(leie)
kjøpskostnader = kjøpesum * 0.025  # Dokumentavgift

# ---------- Oppussing ----------
oppussing_defaults = {
    "riving": 20000,
    "bad": 120000,
    "kjøkken": 100000,
    "overflate": 30000,
    "gulv": 40000,
    "rørlegger": 25000,
    "elektriker": 30000,
    "utvendig": 20000,
}

if "opp_ns" not in st.session_state:
    st.session_state["opp_ns"] = 0
st.session_state["persist"].setdefault("opp", {})

oppussing_total = 0
with st.sidebar.expander("🔨 Oppussing", expanded=False):
    for key, default in oppussing_defaults.items():
        saved_val = st.session_state["persist"]["opp"].get(key, default)
        wkey = f"opp_{key}_{st.session_state['opp_ns']}"
        val = st.number_input(
            key.capitalize(),
            value=int(st.session_state.get(wkey, saved_val)),
            key=wkey,
            step=1000,
            format="%d"
        )
        oppussing_total += int(val)
        st.session_state["persist"]["opp"][key] = int(val)
    st.markdown(f"**Totalt: {oppussing_total:,} kr**")

# ---------- Driftskostnader ----------
driftskostnader_defaults = {
    "forsikring": 8000,
    "strøm": 12000,
    "kommunale avgifter": 9000,
    "internett": 3000,
    "vedlikehold": 8000,
}

if "drift_ns" not in st.session_state:
    st.session_state["drift_ns"] = 0
st.session_state["persist"].setdefault("drift", {})

drift_total = 0
with st.sidebar.expander("💡 Driftskostnader", expanded=False):
    for key, default in driftskostnader_defaults.items():
        saved_val = st.session_state["persist"]["drift"].get(key, default)
        wkey = f"drift_{key}_{st.session_state['drift_ns']}"
        val = st.number_input(
            key.capitalize(),
            value=int(st.session_state.get(wkey, saved_val)),
            key=wkey,
            step=1000,
            format="%d"
        )
        drift_total += int(val)
        st.session_state["persist"]["drift"][key] = int(val)
    st.markdown(f"**Totalt: {drift_total:,} kr**")

# ---------- Lån ----------
lån_defaults = {
    "egenkapital": 300000,
    "rente": 5.0,
    "løpetid": 25,
    "avdragsfri": 2,
    "lånetype": "Annuitetslån",
    "eierform": "Privat",
}
for k, v in lån_defaults.items():
    if k not in st.session_state:
        st.session_state[k] = st.session_state["persist"].get(k, v)

total_investering = kjøpesum + kjøpskostnader + oppussing_total
lånebeløp = max(total_investering - st.session_state["egenkapital"], 0)
st.session_state["lån"] = lånebeløp

with st.sidebar.expander(f"🏦 Lån: {int(st.session_state['lån']):,} kr", expanded=False):
    st.session_state["egenkapital"] = st.number_input("Egenkapital", value=st.session_state["egenkapital"], step=10000)
    st.session_state["rente"] = st.number_input("Rente (%)", value=st.session_state["rente"], step=0.1)
    st.session_state["løpetid"] = st.number_input("Løpetid (år)", value=st.session_state["løpetid"], step=1, min_value=1)
    st.session_state["avdragsfri"] = st.number_input("Avdragsfri (år)", value=st.session_state["avdragsfri"], step=1, min_value=0)
    st.session_state["lånetype"] = st.selectbox("Lånetype", ["Annuitetslån", "Serielån"], index=["Annuitetslån", "Serielån"].index(st.session_state["lånetype"]))
    st.session_state["eierform"] = st.radio("Eierform", ["Privat", "AS"], index=["Privat", "AS"].index(st.session_state["eierform"]))

for k in lån_defaults:
    st.session_state["persist"][k] = st.session_state[k]

# ---------- Beregning ----------
def beregn_lån(lån, rente, løpetid, avdragsfri, lånetype, leie, drift, eierform):
    n  = int(løpetid * 12)
    af = int(avdragsfri * 12)
    r  = rente / 100 / 12
    if lånetype == "Annuitetslån" and r > 0 and (n - af) > 0:
        terminbeløp = lån * (r * (1 + r)**(n - af)) / ((1 + r)**(n - af) - 1)
    else:
        terminbeløp = lån / (n - af) if (n - af) > 0 else 0
    saldo = lån
    restgjeld, avdrag, renter_liste, netto_cf, akk_cf = [], [], [], [], []
    akk = 0.0
    for m in range(n):
        rente_mnd = saldo * r
        if m < af:
            avdrag_mnd = 0.0
            termin = rente_mnd
        elif lånetype == "Serielån" and (n - af) > 0:
            avdrag_mnd = lån / (n - af)
            termin = avdrag_mnd + rente_mnd
        else:
            avdrag_mnd = terminbeløp - rente_mnd
            termin = terminbeløp
        saldo = max(saldo - avdrag_mnd, 0.0)
        netto = leie - (drift / 12.0) - termin
        if eierform == "AS" and netto > 0:
            netto *= (1 - 0.375)
        akk += netto
        restgjeld.append(saldo)
        avdrag.append(avdrag_mnd)
        renter_liste.append(rente_mnd)
        netto_cf.append(netto)
        akk_cf.append(akk)
    return pd.DataFrame({
        "Måned": list(range(1, n + 1)),
        "Restgjeld": restgjeld,
        "Avdrag": avdrag,
        "Renter": renter_liste,
        "Netto cashflow": netto_cf,
        "Akk. cashflow": akk_cf
    }), akk

df, akk = beregn_lån(
    st.session_state["lån"],
    st.session_state["rente"],
    st.session_state["løpetid"],
    st.session_state["avdragsfri"],
    st.session_state["lånetype"],
    leie,
    drift_total,
    st.session_state["eierform"]
)

# === HOVEDINNHOLD (resultater til høyre) ===
st.markdown("---")
col1, col2 = st.columns([1, 1.4])

with col1:
    st.subheader("✨ Resultater")
    st.metric("Total investering", f"{int(total_investering):,} kr")
    st.metric("Brutto yield", f"{(leie * 12 / total_investering) * 100:.2f} %")
    st.metric("Netto yield", f"{((leie * 12 - drift_total) / total_investering) * 100:.2f} %")

    st.subheader("Kontantstrøm (første 60 måneder)")
    st.dataframe(df.head(60), use_container_width=True, height=500)

with col2:
    st.subheader("Grafer")
    st.line_chart(df[["Netto cashflow", "Akk. cashflow"]], use_container_width=True)
    st.line_chart(df[["Renter", "Avdrag"]], use_container_width=True)
    st.line_chart(df["Restgjeld"], use_container_width=True)

# ---------- Grafer til rapport ----------
def _fig_to_base64_png(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")

def _lag_grafer_base64(df):
    vis_mnd = min(24, len(df))
    netto = df["Netto cashflow"].head(vis_mnd).tolist()
    months = list(range(1, vis_mnd + 1))
    fig1 = plt.figure()
    colors = ["#2e7d32" if v >= 0 else "#c62828" for v in netto]
    plt.bar(months, netto, color=colors)
    plt.axhline(0, linestyle="--")
    plt.xlabel("Måned")
    plt.ylabel("Netto cashflow")
    plt.title("Netto cashflow (første 24 mnd)")
    img1_b64 = _fig_to_base64_png(fig1)
    fig2 = plt.figure()
    plt.plot(df["Måned"], df["Akk. cashflow"])
    plt.axhline(0, linestyle="--")
    plt.xlabel("Måned")
    plt.ylabel("Akkumulert cashflow")
    plt.title("Akkumulert cashflow")
    img2_b64 = _fig_to_base64_png(fig2)
    return img1_b64, img2_b64

# ---------- HTML-rapport ----------
def lag_presentasjon_html():
    img_nett_b64, img_akk_b64 = _lag_grafer_base64(df)
    finn_html = f'<p><a href="{finn_url}" target="_blank">🔗 Åpne Finn-annonse</a></p>' if finn_url else ""
    brutto_yield = (leie * 12 / total_investering) * 100 if total_investering else 0
    netto_yield = ((leie * 12 - drift_total) / total_investering) * 100 if total_investering else 0
    return f"""
    <html>
    <body>
    <h1>{proj_navn}</h1>
    {finn_html}
    <p>Kjøpesum: {kjøpesum:,.0f} kr</p>
    <p>Dokumentavgift: {kjøpskostnader:,.0f} kr</p>
    <p>Oppussing: {oppussing_total:,.0f} kr</p>
    <p>Drift: {drift_total:,.0f} kr</p>
    <p>Total investering: {total_investering:,.0f} kr</p>
    <p>Brutto yield: {brutto_yield:.2f}%</p>
    <p>Netto yield: {netto_yield:.2f}%</p>
    <img src="data:image/png;base64,{img_nett_b64}"/>
    <img src="data:image/png;base64,{img_akk_b64}"/>
    </body>
    </html>
    """.encode("utf-8")

rapport_bytes = lag_presentasjon_html()
st.download_button("📄 Last ned presentasjon (HTML)", data=rapport_bytes, file_name="rapport.html", mime="text/html")

# ---------- Lagre persist til fil ----------
if st.session_state["_dirty"]:
    _save_persist(st.session_state["persist"])
    st.session_state["_dirty"] = False
