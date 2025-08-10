import streamlit as st
import pandas as pd

# ------------------ Layout og stil ------------------
st.set_page_config(layout="wide")
st.markdown("""
    <style>
    /* Gjør scrollbaren mer synlig for dataframe */
    div[data-testid="stDataFrameScrollable"]::-webkit-scrollbar { width: 16px; }
    div[data-testid="stDataFrameScrollable"]::-webkit-scrollbar-thumb {
        background-color: #444; border-radius: 8px;
    }
    div[data-testid="stDataFrameScrollable"]::-webkit-scrollbar-thumb:hover { background-color: #222; }
    </style>
""", unsafe_allow_html=True)

st.title("AMO Eiendomskalkulator")

# ------------------ Sidebar: grunninntasting ------------------
st.sidebar.header("🧾 Eiendomsinfo")
# --- Prosjektnavn + Finn-annonse ---
proj_navn = st.sidebar.text_input(
    "Prosjektnavn",
    value=st.session_state.get("prosjekt_navn", "Eiendomsprosjekt"),
)
st.session_state["prosjekt_navn"] = proj_navn

finn_url = st.sidebar.text_input(
    "Finn-annonse (URL)",
    value=st.session_state.get("finn_url", ""),
    placeholder="https://www.finn.no/realestate/..."
)
# enkel normalisering
if finn_url and not finn_url.startswith(("http://", "https://")):
    finn_url = "https://" + finn_url
st.session_state["finn_url"] = finn_url
kjøpesum = st.sidebar.number_input("Kjøpesum", value=4_000_000, step=100_000)
leie = st.sidebar.number_input("Leieinntekter / mnd", value=22_000)
Dokumentavgift = kjøpesum * 0.025  # 2.5 % kjøpsomkostninger

# ===========================
# OPPUSSING (RERUN-FREE, ROBUST)
# ===========================
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

def _sum_section(prefix: str, defaults: dict, ns: int, zero_mode: bool) -> int:
    """Summerer verdier for en seksjon før UI rendres.
    Bruker eksisterende widget-keys hvis de finnes, ellers defaults.
    Returnerer heltall for pen tittel.
    """
    if zero_mode:
        return 0
    total = 0
    for key, default in defaults.items():
        wkey = f"{prefix}_{key}_{ns}"
        total += st.session_state.get(wkey, default)
    return int(total)

def sum_namespace(prefix: str, defaults: dict, ns: int) -> int:
    total = 0
    for key in defaults:
        wkey = f"{prefix}_{key}_{ns}"
        total += int(st.session_state.get(wkey, 0) or 0)
    return total

def sum_namespace(prefix: str, defaults: dict, ns: int) -> int:
    s = 0
    for k in defaults:
        s += int(st.session_state.get(f"{prefix}_{k}_{ns}", 0) or 0)
    return s

def sum_namespace(prefix: str, defaults: dict, ns: int) -> int:
    total = 0
    for key in defaults:
        total += int(st.session_state.get(f"{prefix}_{key}_{ns}", 0) or 0)
    return total

# --- Ekspander-styring ---
def expand_section(section: str):
    st.session_state[f"{section}_expanded"] = True

def reset_and_expand(section: str, reset_flag: str):
    st.session_state[reset_flag] = True
    st.session_state[f"{section}_expanded"] = True

# init expander-flagg (start lukket)
for _flag in ("opp_expanded", "drift_expanded"):
    if _flag not in st.session_state:
        st.session_state[_flag] = False

# ---- Oppussing pre-reset ----
if "opp_ns" not in st.session_state:
    st.session_state["opp_ns"] = 0
if "opp_reset_request" not in st.session_state:
    st.session_state["opp_reset_request"] = False

if st.session_state["opp_reset_request"]:
    st.session_state["opp_ns"] += 1   # nye keys → 0-verdier
    st.session_state["opp_reset_request"] = False

# ---- Driftskostnader pre-reset ----
if "drift_ns" not in st.session_state:
    st.session_state["drift_ns"] = 0
if "drift_reset_request" not in st.session_state:
    st.session_state["drift_reset_request"] = False

if st.session_state["drift_reset_request"]:
    st.session_state["drift_ns"] += 1
    st.session_state["drift_reset_request"] = False

# ===========================
# 🔨 Oppussing (instant reset uten rerun)
# ===========================
# Init namespace
if "opp_ns" not in st.session_state:
    st.session_state["opp_ns"] = 0

# Sum for tittelvisning inni boksen (ikke i label)
opp_title_total = sum_namespace("opp", oppussing_defaults, st.session_state["opp_ns"])

with st.sidebar.expander("🔨 Oppussing", expanded=st.session_state["opp_expanded"]):
    st.caption(f"**Sum oppussing:** {opp_title_total:,} kr")

    st.button(
        "Tilbakestill oppussing",
        key="btn_reset_opp",
        on_click=reset_and_expand,
        args=("opp", "opp_reset_request"),   # sett reset-flagget og hold åpen
    )

    ns = st.session_state["opp_ns"]
    oppussing_total = 0
    for key, default in oppussing_defaults.items():
        wkey = f"opp_{key}_{ns}"
        startverdi = st.session_state.get(wkey, default if ns == 0 else 0)
        val = st.number_input(
            key.capitalize(),
            value=startverdi,
            key=wkey,
            step=1000,
            format="%d",
            on_change=expand_section,        # <- hold åpen når Enter trykkes
            args=("opp",),
        )
        oppussing_total += val

    st.markdown(f"**Totalt: {int(oppussing_total):,} kr**")


# ===========================
# DRIFTSKOSTNADER (RERUN-FREE, ROBUST)
# ===========================
driftskostnader_defaults = {
    "forsikring": 8000,
    "strøm": 12000,
    "kommunale avgifter": 9000,
    "internett": 3000,
    "vedlikehold": 8000,
}

# ===========================
# 💡 Driftskostnader (instant reset uten rerun)
# ===========================
# Init namespace første gang
# Init namespace
if "drift_ns" not in st.session_state:
    st.session_state["drift_ns"] = 0

# Reset-knapp FØR expanderen
drift_title_total = sum_namespace("drift", driftskostnader_defaults, st.session_state["drift_ns"])

with st.sidebar.expander("💡 Driftskostnader", expanded=st.session_state["drift_expanded"]):
    st.caption(f"**Sum driftskostnader:** {drift_title_total:,} kr")

    st.button(
        "Tilbakestill driftskostnader",
        key="btn_reset_drift",
        on_click=reset_and_expand,
        args=("drift", "drift_reset_request"),
    )

    ns = st.session_state["drift_ns"]
    drift_total = 0
    for key, default in driftskostnader_defaults.items():
        wkey = f"drift_{key}_{ns}"
        startverdi = st.session_state.get(wkey, default if ns == 0 else 0)
        val = st.number_input(
            key.capitalize(),
            value=startverdi,
            key=wkey,
            step=1000,
            format="%d",
            on_change=expand_section,      # <- hold åpen når Enter trykkes
            args=("drift",),
        )
        drift_total += val

    st.markdown(f"**Totalt: {int(drift_total):,} kr**")


# ------------------ Lån og finansiering ------------------
# Standardverdier i state kun første gang
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
        st.session_state[k] = v

# Total investering nå
total_investering = kjøpesum + kjøpskostnader + oppussing_total
lånebeløp = max(total_investering - st.session_state["egenkapital"], 0)
st.session_state["lån"] = lånebeløp  # tilgjengelig for beregning

with st.sidebar.expander(f"🏦 Lån: {int(st.session_state['lån']):,} kr", expanded=False):
    st.session_state["egenkapital"] = st.number_input(
        "Egenkapital", value=st.session_state["egenkapital"], min_value=0, step=10000
    )
    # oppdater lånebeløp live
    st.session_state["lån"] = max(total_investering - st.session_state["egenkapital"], 0)

    st.session_state["rente"]     = st.number_input("Rente (%)", value=st.session_state["rente"], step=0.1)
    st.session_state["løpetid"]   = st.number_input("Løpetid (år)", value=st.session_state["løpetid"], step=1, min_value=1)
    st.session_state["avdragsfri"]= st.number_input("Avdragsfri (år)", value=st.session_state["avdragsfri"], step=1, min_value=0)
    st.session_state["lånetype"]  = st.selectbox("Lånetype", ["Annuitetslån", "Serielån"],
                                  index=["Annuitetslån", "Serielån"].index(st.session_state["lånetype"]))
    st.session_state["eierform"]  = st.radio("Eierform", ["Privat", "AS"],
                                  index=["Privat", "AS"].index(st.session_state["eierform"]))

# ------------------ Lånekalkyle ------------------
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

    df = pd.DataFrame({
        "Måned": list(range(1, n + 1)),
        "Restgjeld": restgjeld,
        "Avdrag": avdrag,
        "Renter": renter_liste,
        "Netto cashflow": netto_cf,
        "Akk. cashflow": akk_cf
    })
    return df, akk

# ------------------ Beregning / Resultater ------------------
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

st.subheader("✨ Resultater")
st.metric("Total investering", f"{int(total_investering):,} kr")
st.metric("Brutto yield", f"{(leie * 12 / total_investering) * 100:.2f} %")
st.metric("Netto yield", f"{((leie * 12 - drift_total) / total_investering) * 100:.2f} %")

st.subheader("Kontantstrøm (første 60 måneder)")
st.dataframe(df.head(60), use_container_width=True, height=500)

st.subheader("Grafer")
st.line_chart(df[["Netto cashflow", "Akk. cashflow"]])
st.line_chart(df[["Renter", "Avdrag"]])
st.line_chart(df["Restgjeld"])

import base64
from io import BytesIO
import matplotlib.pyplot as plt

def _fig_to_base64_png(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")

def _lag_grafer_base64(df):
    # 1) Netto cashflow, 24 mnd søyler (grønn/rød)
    vis_mnd = min(24, len(df))
    netto = df["Netto cashflow"].head(vis_mnd).tolist()
    months = list(range(1, vis_mnd + 1))

    fig1 = plt.figure()
    colors = ["#2e7d32" if v >= 0 else "#c62828" for v in netto]
    plt.bar(months, netto, edgecolor="none", linewidth=0, color=colors)
    plt.axhline(0, linestyle="--")
    plt.xlabel("Måned")
    plt.ylabel("Netto cashflow")
    plt.title("Netto cashflow (første 24 mnd)")
    img1_b64 = _fig_to_base64_png(fig1)

    # 2) Akkumulert cashflow linje
    fig2 = plt.figure()
    plt.plot(df["Måned"], df["Akk. cashflow"])
    plt.axhline(0, linestyle="--")
    plt.xlabel("Måned")
    plt.ylabel("Akkumulert cashflow")
    plt.title("Akkumulert cashflow")
    img2_b64 = _fig_to_base64_png(fig2)

    return img1_b64, img2_b64

def lag_presentasjon_html(
    df: pd.DataFrame,
    kjøpesum: int,
    kjøpskostnader: int,
    oppussing_total: int,
    drift_total: int,
    total_investering: int,
    leie: int,
    lån: int,
    rente: float,
    løpetid: int,
    avdragsfri: int,
    lånetype: str,
    eierform: str,
    prosjekt_navn: str = "Eiendomsprosjekt",
    finn_url: str = "",
) -> bytes:
    # Lag grafbilder (base64)
    img_nett_b64, img_akk_b64 = _lag_grafer_base64(df)

    # Nøkkeltall
    brutto_yield = (leie * 12 / total_investering) * 100 if total_investering else 0.0
    netto_yield  = ((leie * 12 - drift_total) / total_investering) * 100 if total_investering else 0.0

    # Tabell (første 24 mnd for kompakthet)
    vis_mnd = min(24, len(df))
    tab_rows = []
    for i in range(vis_mnd):
        r = df.iloc[i]
        tab_rows.append(
            f"<tr>"
            f"<td>{int(r['Måned'])}</td>"
            f"<td>{r['Restgjeld']:,.0f}</td>"
            f"<td>{r['Avdrag']:,.0f}</td>"
            f"<td>{r['Renter']:,.0f}</td>"
            f"<td>{r['Netto cashflow']:,.0f}</td>"
            f"<td>{r['Akk. cashflow']:,.0f}</td>"
            f"</tr>"
        )

    finn_html = (
        f'<p><a href="{finn_url}" target="_blank" '
        f'style="text-decoration:none;padding:8px 12px;border:1px solid #0b63ce;'
        f'border-radius:8px;color:#0b63ce;">🔗 Åpne Finn-annonse</a></p>'
        if finn_url else ""
    )

    html = f"""<!DOCTYPE html>
<html lang="no">
<head>
<meta charset="utf-8" />
<title>{prosjekt_navn} – Presentasjon</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 24px; color: #111; }}
  h1, h2 {{ margin: 0 0 8px 0; }}
  h1 {{ font-size: 28px; }}
  h2 {{ font-size: 20px; margin-top: 24px; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
  .card {{ border: 1px solid #eee; border-radius: 12px; padding: 16px; box-shadow: 0 1px 6px rgba(0,0,0,0.04); }}
  .kpi {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 8px; }}
  .kpi div {{ background: #fafafa; border: 1px solid #eee; border-radius: 10px; padding: 12px; }}
  .muted {{ color: #555; font-size: 12px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
  th, td {{ border-bottom: 1px solid #eee; padding: 6px 8px; text-align: right; }}
  th:first-child, td:first-child {{ text-align: left; }}
  img {{ max-width: 100%; height: auto; border-radius: 10px; border: 1px solid #eee; }}
  .badge {{ background: #eef6ff; color: #0b63ce; font-weight: 600; padding: 4px 8px; border-radius: 999px; display: inline-block; font-size: 12px; }}
</style>
</head>
<body>

<h1>{prosjekt_navn}</h1>
<p class="muted">Generert automatisk fra AMO Eiendomskalkulator</p>
{finn_html}

<div class="kpi">
  <div><div class="muted">Kjøpesum</div><div><strong>{kjøpesum:,.0f} kr</strong></div></div>
  <div><div class="muted">Kjøpskostnader</div><div><strong>{kjøpskostnader:,.0f} kr</strong></div></div>
  <div><div class="muted">Oppussing</div><div><strong>{oppussing_total:,.0f} kr</strong></div></div>
  <div><div class="muted">Driftskostn./år</div><div><strong>{drift_total:,.0f} kr</strong></div></div>
  <div><div class="muted">Total investering</div><div><strong>{total_investering:,.0f} kr</strong></div></div>
  <div><div class="muted">Leie/mnd</div><div><strong>{leie:,.0f} kr</strong></div></div>
  <div><div class="muted">Lån</div><div><strong>{lån:,.0f} kr</strong></div></div>
  <div><div class="muted">Brutto yield</div><div><strong>{brutto_yield:.2f} %</strong></div></div>
  <div><div class="muted">Netto yield</div><div><strong>{netto_yield:.2f} %</strong></div></div>
</div>

<h2>Finansiering</h2>
<p class="muted">
  Lånetype: <span class="badge">{lånetype}</span> &nbsp; | &nbsp; 
  Rente: <strong>{rente:.2f}%</strong> &nbsp; | &nbsp; 
  Løpetid: <strong>{løpetid} år</strong> &nbsp; | &nbsp; 
  Avdragsfri: <strong>{avdragsfri} år</strong> &nbsp; | &nbsp; 
  Eierform: <strong>{eierform}</strong>
</p>

<div class="grid">
  <div class="card">
    <h2>Netto cashflow (24 mnd)</h2>
    <img src="data:image/png;base64,{img_nett_b64}" alt="Netto cashflow søylediagram" />
  </div>
  <div class="card">
    <h2>Akkumulert cashflow</h2>
    <img src="data:image/png;base64,{img_akk_b64}" alt="Akkumulert cashflow linjediagram" />
  </div>
</div>

<h2>Kontantstrøm – første 24 måneder</h2>
<div class="card">
<table>
  <thead>
    <tr>
      <th>Mnd</th>
      <th>Restgjeld</th>
      <th>Avdrag</th>
      <th>Renter</th>
      <th>Netto</th>
      <th>Akk.</th>
    </tr>
  </thead>
  <tbody>
    {''.join(tab_rows)}
  </tbody>
</table>
<p class="muted">Full tidsserie kan eksporteres fra appen (CSV/Excel).</p>
</div>

</body>
</html>
"""
    return html.encode("utf-8")

# === UI-knapp i Streamlit (legg etter at df og nøkkeltall er beregnet) ===
rapport_bytes = lag_presentasjon_html(
    df=df,
    kjøpesum=kjøpesum,
    kjøpskostnader=int(kjøpesum * 0.025),
    oppussing_total=int(oppussing_total),
    drift_total=int(drift_total),
    total_investering=int(total_investering),
    leie=int(leie),
    lån=int(st.session_state["lån"]),
    rente=float(st.session_state["rente"]),
    løpetid=int(st.session_state["løpetid"]),
    avdragsfri=int(st.session_state["avdragsfri"]),
    lånetype=st.session_state["lånetype"],
    eierform=st.session_state["eierform"],
    prosjekt_navn=st.session_state.get("prosjekt_navn", "Eiendomsprosjekt"),
    finn_url=st.session_state.get("finn_url", ""),
)

st.download_button(
    "📄 Last ned presentasjon (HTML)",
    data=rapport_bytes,
    file_name="eiendomsrapport.html",
    mime="text/html",
    use_container_width=True,
)
st.caption("Tips: Åpne HTML-filen i nettleser → Print → Save as PDF for å lagre som PDF.")
