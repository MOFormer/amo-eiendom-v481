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

# init session_state for persist + dirty
if "persist" not in st.session_state:
    st.session_state["persist"] = _load_persist()
if "_dirty" not in st.session_state:
    st.session_state["_dirty"] = False

def mark_dirty():
    st.session_state["_dirty"] = True
# ----------------------------------------

st.set_page_config(layout="wide")
st.title("AMO Eiendomskalkulator")

# --- Pending profile load (må kjøres før widgets bygges) ---
if "pending_profile_name" in st.session_state and st.session_state["pending_profile_name"]:
    sel = st.session_state["pending_profile_name"]
    p = st.session_state["profiles"].get(sel, {})

    # Grunnfelter -> persist
    st.session_state["persist"]["prosjekt_navn"] = p.get("prosjekt_navn", sel)
    st.session_state["persist"]["finn_url"]      = p.get("finn_url", "")
    st.session_state["persist"]["note"]          = p.get("note", "")

    # Kjøpesum/leie
    st.session_state["persist"]["kjøpesum"] = p.get("kjøpesum", 0)
    st.session_state["persist"]["leie"]     = p.get("leie", 0)

    # Oppussing/drift
    st.session_state["persist"]["opp"]   = p.get("oppussing", {})
    st.session_state["persist"]["drift"] = p.get("drift", {})

    # Lån
    st.session_state["egenkapital"] = p.get("egenkapital", st.session_state.get("egenkapital", 300000))
    st.session_state["rente"]       = p.get("rente",       st.session_state.get("rente", 5.0))
    st.session_state["løpetid"]     = p.get("løpetid",     st.session_state.get("løpetid", 25))
    st.session_state["avdragsfri"]  = p.get("avdragsfri",  st.session_state.get("avdragsfri", 0))
    st.session_state["lånetype"]    = p.get("lånetype",    st.session_state.get("lånetype", "Annuitetslån"))
    st.session_state["eierform"]    = p.get("eierform",    st.session_state.get("eierform", "Privat"))

    # Sørg for at neste render bruker riktige widget-verdier:
    st.session_state["prosjektnavn_input"] = st.session_state["persist"]["prosjekt_navn"]
    st.session_state["finn_url_input"]     = st.session_state["persist"]["finn_url"]

    # (Hvis du bruker ns/expanders): bump og åpne
    st.session_state["opp_ns"]   = st.session_state.get("opp_ns", 0) + 1
    st.session_state["drift_ns"] = st.session_state.get("drift_ns", 0) + 1
    st.session_state["opp_expanded"]   = True
    st.session_state["drift_expanded"] = True

    # Tøm pending og rerun FØR widgets rendres
    st.session_state["pending_profile_name"] = ""
    st.rerun()

# ---------- Sidebar: Grunninfo ----------
st.sidebar.header("🧾 Eiendomsinfo")

proj_navn = st.sidebar.text_input(
    "Prosjektnavn",
    key="prosjektnavn_input",  # ← fast key
    value=st.session_state["persist"].get("prosjekt_navn", "Eiendomsprosjekt"),
    on_change=mark_dirty,
)
st.session_state["persist"]["prosjekt_navn"] = proj_navn

finn_url = st.sidebar.text_input(
    "Finn-annonse (URL)",
    key="finn_url_input",  # ← fast key
    value=st.session_state["persist"].get("finn_url", ""),
    on_change=mark_dirty,
    placeholder="https://www.finn.no/realestate/..."
)
if finn_url and not finn_url.startswith(("http://", "https://")):
    finn_url = "https://" + finn_url
st.session_state["persist"]["finn_url"] = finn_url

note = st.sidebar.text_area(
    "Prosjektnotater",
    value=st.session_state["persist"].get("note", ""),
    on_change=mark_dirty,
    height=100,
    placeholder="Skriv inn dine notater om prosjektet..."
)
st.session_state["persist"]["note"] = note
# enkel normalisering for rask lim/skriv
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
kjøpskostnader = int(kjøpesum * 0.025)  # Dokumentavgift

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
st.session_state["persist"].setdefault("opp", {})

oppussing_total = 0
with st.sidebar.expander("🔨 Oppussing", expanded=False):
    for key, default in oppussing_defaults.items():
        saved_val = st.session_state["persist"]["opp"].get(key, default)
        wkey = f"opp_{key}"
        val = st.number_input(
            key.capitalize(),
            value=int(st.session_state.get(wkey, saved_val)),
            key=wkey,
            step=1000,
            format="%d"
        )
        val = int(val)
        oppussing_total += val
        # speil til persist + mark dirty hvis endret
        if st.session_state["persist"]["opp"].get(key) != val:
            st.session_state["persist"]["opp"][key] = val
            mark_dirty()
    st.markdown(f"**Totalt: {oppussing_total:,} kr**")

# ---------- Driftskostnader ----------
driftskostnader_defaults = {
    "forsikring": 8000,
    "strøm": 12000,
    "kommunale avgifter": 9000,
    "internett": 3000,
    "vedlikehold": 8000,
}
st.session_state["persist"].setdefault("drift", {})

drift_total = 0
with st.sidebar.expander("💡 Driftskostnader", expanded=False):
    for key, default in driftskostnader_defaults.items():
        saved_val = st.session_state["persist"]["drift"].get(key, default)
        wkey = f"drift_{key}"
        val = st.number_input(
            key.capitalize(),
            value=int(st.session_state.get(wkey, saved_val)),
            key=wkey,
            step=1000,
            format="%d"
        )
        val = int(val)
        drift_total += val
        if st.session_state["persist"]["drift"].get(key) != val:
            st.session_state["persist"]["drift"][key] = val
            mark_dirty()
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
# init lån-felter fra persist hvis finnes
for k, v in lån_defaults.items():
    if k not in st.session_state:
        st.session_state[k] = st.session_state["persist"].get(k, v)

total_investering = int(kjøpesum + kjøpskostnader + oppussing_total)
lånebeløp = max(total_investering - int(st.session_state["egenkapital"]), 0)
st.session_state["lån"] = lånebeløp

with st.sidebar.expander(f"🏦 Lån: {int(st.session_state['lån']):,} kr", expanded=False):
    st.session_state["egenkapital"] = st.number_input("Egenkapital", value=int(st.session_state["egenkapital"]), step=10000)
    st.session_state["rente"] = st.number_input("Rente (%)", value=float(st.session_state["rente"]), step=0.1)
    st.session_state["løpetid"] = st.number_input("Løpetid (år)", value=int(st.session_state["løpetid"]), step=1, min_value=1)
    st.session_state["avdragsfri"] = st.number_input("Avdragsfri (år)", value=int(st.session_state["avdragsfri"]), step=1, min_value=0)
    st.session_state["lånetype"] = st.selectbox("Lånetype", ["Annuitetslån", "Serielån"], index=["Annuitetslån", "Serielån"].index(st.session_state["lånetype"]))
    st.session_state["eierform"] = st.radio("Eierform", ["Privat", "AS"], index=["Privat", "AS"].index(st.session_state["eierform"]))

# oppdater persist for lån
for k in lån_defaults:
    if st.session_state["persist"].get(k) != st.session_state[k]:
        st.session_state["persist"][k] = st.session_state[k]
        mark_dirty()

# oppdater lånebeløp etter ev. endringer
total_investering = int(kjøpesum + kjøpskostnader + oppussing_total)
st.session_state["lån"] = max(total_investering - int(st.session_state["egenkapital"]), 0)

# ---------- Beregning ----------
def beregn_lån(lån, rente, løpetid, avdragsfri, lånetype, leie, drift, eierform):
    n  = int(løpetid * 12)
    af = int(avdragsfri * 12)
    r  = float(rente) / 100 / 12
    if lånetype == "Annuitetslån" and r > 0 and (n - af) > 0:
        terminbeløp = lån * (r * (1 + r)**(n - af)) / ((1 + r)**(n - af) - 1)
    else:
        terminbeløp = lån / (n - af) if (n - af) > 0 else 0
    saldo = float(lån)
    restgjeld, avdrag, renter_liste, netto_cf, akk_cf = [], [], [], [], []
    akk = 0.0
    for m in range(n):
        rente_mnd = saldo * r
        if m < af:
            avdrag_mnd = 0.0
            termin = rente_mnd
        elif lånetype == "Serielån" and (n - af) > 0:
            avdrag_mnd = float(lån) / (n - af)
            termin = avdrag_mnd + rente_mnd
        else:
            avdrag_mnd = terminbeløp - rente_mnd
            termin = terminbeløp
        saldo = max(saldo - avdrag_mnd, 0.0)
        netto = float(leie) - (float(drift) / 12.0) - termin
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
    int(st.session_state["lån"]),
    float(st.session_state["rente"]),
    int(st.session_state["løpetid"]),
    int(st.session_state["avdragsfri"]),
    st.session_state["lånetype"],
    int(leie),
    int(drift_total),
    st.session_state["eierform"]
)

# ===========================
# ENKEL LAGRE / LAST / SLETT
# ===========================
existing = ["(Velg)"] + sorted(st.session_state["profiles"].keys())
sel = st.sidebar.selectbox("Åpne / Slett profil", options=existing, index=0)

def _queue_load_profile(name: str):
    st.session_state["pending_profile_name"] = name

if sel != "(Velg)":
    st.sidebar.button("📂 Last profil", on_click=_queue_load_profile, args=(sel,))
    st.sidebar.button("🗑️ Slett profil", on_click=lambda: (
        st.session_state["profiles"].pop(sel, None),
        _save_profiles(st.session_state["profiles"])
    ))

# Navn på profil (default: prosjektnavn eller generisk)
profile_name = st.sidebar.text_input(
    "Profilnavn",
    value=st.session_state.get("prosjekt_navn") or st.session_state["persist"].get("prosjekt_navn", "Eiendomsprosjekt")
)

def _current_profile_payload() -> dict:
    # Pakk sammen “gjeldende prosjekt” til en dict
    return {
        "prosjekt_navn": st.session_state["persist"].get("prosjekt_navn", profile_name),
        "finn_url":      st.session_state["persist"].get("finn_url", ""),
        "note":          st.session_state["persist"].get("note", ""),
        "kjøpesum":      int(kjøpesum),
        "leie":          int(leie),
        "dokumentavgift": int(kjøpesum * 0.025),
        "oppussing":     {k: int(st.session_state["persist"].get("opp", {}).get(k, v)) for k, v in oppussing_defaults.items()},
        "drift":         {k: int(st.session_state["persist"].get("drift", {}).get(k, v)) for k, v in driftskostnader_defaults.items()},
        # Lån
        "egenkapital":   int(st.session_state["egenkapital"]),
        "rente":         float(st.session_state["rente"]),
        "løpetid":       int(st.session_state["løpetid"]),
        "avdragsfri":    int(st.session_state["avdragsfri"]),
        "lånetype":      st.session_state["lånetype"],
        "eierform":      st.session_state["eierform"],
    }

# Lagre
if st.sidebar.button("💾 Lagre profil"):
    name = profile_name.strip() or "Uten navn"
    st.session_state["profiles"][name] = _current_profile_payload()
    _save_profiles(st.session_state["profiles"])
    st.sidebar.success(f"Lagret: {name}")

# Velg eksisterende profil
existing = ["(Velg)"] + sorted(st.session_state["profiles"].keys())
sel = st.sidebar.selectbox("Åpne / Slett profil", options=existing, index=0)

# Last valgt profil (putter verdiene inn i appen og persist)
if sel != "(Velg)" and st.sidebar.button("📂 Last profil"):
    p = st.session_state["profiles"][sel]

    # Grunnfelter -> persist
    st.session_state["persist"]["prosjekt_navn"] = p.get("prosjekt_navn", sel)
    st.session_state["persist"]["finn_url"]      = p.get("finn_url", "")
    st.session_state["persist"]["note"]          = p.get("note", "")

    # Tving oppdatering av *widgetene* (tekstfeltene) ved å sette deres keys
    st.session_state["prosjektnavn_input"] = st.session_state["persist"]["prosjekt_navn"]
    st.session_state["finn_url_input"]     = st.session_state["persist"]["finn_url"]

    # Kjøpesum/leie -> persist
    st.session_state["persist"]["kjøpesum"] = p.get("kjøpesum", 0)
    st.session_state["persist"]["leie"]     = p.get("leie", 0)

    # Oppussing/drift -> persist
    st.session_state["persist"]["opp"]   = p.get("oppussing", {})
    st.session_state["persist"]["drift"] = p.get("drift", {})

    # Lån -> direkte i session_state (widgets leser herfra)
    st.session_state["egenkapital"] = p.get("egenkapital", st.session_state["egenkapital"])
    st.session_state["rente"]       = p.get("rente",       st.session_state["rente"])
    st.session_state["løpetid"]     = p.get("løpetid",     st.session_state["løpetid"])
    st.session_state["avdragsfri"]  = p.get("avdragsfri",  st.session_state["avdragsfri"])
    st.session_state["lånetype"]    = p.get("lånetype",    st.session_state["lånetype"])
    st.session_state["eierform"]    = p.get("eierform",    st.session_state["eierform"])

    # Remount inputs: (om du bruker namespacing et annet sted)
    st.session_state["opp_ns"]   = st.session_state.get("opp_ns", 0) + 1
    st.session_state["drift_ns"] = st.session_state.get("drift_ns", 0) + 1
    st.session_state["opp_expanded"]   = True
    st.session_state["drift_expanded"] = True

    # (valgfritt) marker dirty og lagre profiler til fil
    st.session_state["_dirty"] = True
    _save_profiles(st.session_state["profiles"])
    st.sidebar.info(f"Lastet: {sel}")

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

# ---------- Grafer til rapport (helper) ----------
def _fig_to_base64_png(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")

def _charts_base64(df, kjøpesum, dokumentavgift, oppussing_total):
    # Netto cashflow – første 24 mnd, fargekodet
    vis_mnd = min(24, len(df))
    months = list(range(1, vis_mnd + 1))
    netto = df["Netto cashflow"].head(vis_mnd).tolist()

    fig1 = plt.figure()
    colors = ["#2e7d32" if v >= 0 else "#c62828" for v in netto]
    plt.bar(months, netto, color=colors, linewidth=0)
    plt.axhline(0, linestyle="--", linewidth=1)
    plt.xlabel("Måned"); plt.ylabel("Netto cashflow"); plt.title("Netto cashflow (første 24 mnd)")
    img_nett_b64 = _fig_to_base64_png(fig1)

    # Akkumulert cashflow – hele perioden
    fig2 = plt.figure()
    plt.plot(df["Måned"], df["Akk. cashflow"])
    plt.axhline(0, linestyle="--", linewidth=1)
    plt.xlabel("Måned"); plt.ylabel("Akkumulert cashflow"); plt.title("Akkumulert cashflow")
    img_akk_b64 = _fig_to_base64_png(fig2)

    # Returnér KUN to bilder nå
    return img_nett_b64, img_akk_b64

# ---------- HTML-rapport ----------
def lag_presentasjon_html(
    df: pd.DataFrame,
    kjøpesum: int,
    dokumentavgift: int,
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
    note: str = "",
) -> bytes:
    # Grafer
    img_nett_b64, img_akk_b64 = _charts_base64(df, kjøpesum, dokumentavgift, oppussing_total)

    # KPI’er
    brutto_yield = (leie * 12 / total_investering) * 100 if total_investering else 0
    netto_yield  = ((leie * 12 - drift_total) / total_investering) * 100 if total_investering else 0

    finn_html = (
        f'<p><a href="{finn_url}" target="_blank" '
        f'style="text-decoration:none;padding:8px 12px;border:1px solid #0b63ce;'
        f'border-radius:8px;color:#0b63ce;">🔗 Åpne Finn-annonse</a></p>'
        if finn_url else ""
    )

    def _safe(s: str) -> str:
        # veldig enkel escaping for HTML
        return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    html = f"""
<!DOCTYPE html>
<html lang="no">
<head>
<meta charset="utf-8" />
<title>{_safe(prosjekt_navn)} – Presentasjon</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 24px; color: #111; }}
  h1, h2 {{ margin: 0 0 8px 0; }}
  h1 {{ font-size: 28px; }}
  h2 {{ font-size: 20px; margin-top: 24px; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
  .card {{ border: 1px solid #eee; border-radius: 12px; padding: 16px; box-shadow: 0 1px 6px rgba(0,0,0,0.04); }}
  .kpi {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }}
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

<h1>{_safe(prosjekt_navn)}</h1>
<p class="muted">Generert automatisk fra AMO Eiendomskalkulator</p>
{finn_html}

{"<div class='card'><h2>Notater</h2><p>" + _safe(note).replace("\\n","<br>") + "</p></div>" if note else ""}

<div class="kpi">
  <div><div class="muted">Kjøpesum</div><div><strong>{kjøpesum:,.0f} kr</strong></div></div>
  <div><div class="muted">Dokumentavgift</div><div><strong>{dokumentavgift:,.0f} kr</strong></div></div>
  <div><div class="muted">Oppussing</div><div><strong>{oppussing_total:,.0f} kr</strong></div></div>
  <div><div class="muted">Driftskostn./år</div><div><strong>{drift_total:,.0f} kr</strong></div></div>
  <div><div class="muted">Total investering</div><div><strong>{total_investering:,.0f} kr</strong></div></div>
  <div><div class="muted">Leie/mnd</div><div><strong>{leie:,.0f} kr</strong></div></div>
  <div><div class="muted">Egenkapital</div><div><strong>{st.session_state["egenkapital"]:,.0f} kr</strong></div></div>
  <div><div class="muted">Rente</div><div><strong>{rente:.2f} %</strong></div></div>
  <div><div class="muted">Brutto yield</div><div><strong>{brutto_yield:.2f} %</strong></div></div>
  <div><div class="muted">Netto yield</div><div><strong>{netto_yield:.2f} %</strong></div></div>
</div>

<h2>Finansiering</h2>
<p class="muted">
  Lånetype: <span class="badge">{_safe(lånetype)}</span> &nbsp; | &nbsp;
  Rente: <strong>{rente:.2f}%</strong> &nbsp; | &nbsp;
  Løpetid: <strong>{løpetid} år</strong> &nbsp; | &nbsp;
  Avdragsfri: <strong>{avdragsfri} år</strong> &nbsp; | &nbsp;
  Eierform: <strong>{_safe(eierform)}</strong>
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
"""
    # Tabellrader (24 mnd)
    vis_mnd = min(24, len(df))
    for i in range(vis_mnd):
        r = df.iloc[i]
        html += (
            f"<tr>"
            f"<td>{int(r['Måned'])}</td>"
            f"<td>{r['Restgjeld']:,.0f}</td>"
            f"<td>{r['Avdrag']:,.0f}</td>"
            f"<td>{r['Renter']:,.0f}</td>"
            f"<td>{r['Netto cashflow']:,.0f}</td>"
            f"<td>{r['Akk. cashflow']:,.0f}</td>"
            f"</tr>"
        )

    html += """
  </tbody>
</table>
<p class="muted">Full tidsserie kan eksporteres fra appen (CSV/Excel).</p>
</div>

</body>
</html>
"""
    return html.encode("utf-8")

def projektsafe(s: str) -> str:
    # veldig enkel HTML-escape for tittelen
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def build_rows(df: pd.DataFrame) -> str:
    vis_mnd = min(24, len(df))
    out = []
    for i in range(vis_mnd):
        r = df.iloc[i]
        out.append(
            f"<tr>"
            f"<td>{int(r['Måned'])}</td>"
            f"<td>{r['Restgjeld']:,.0f}</td>"
            f"<td>{r['Avdrag']:,.0f}</td>"
            f"<td>{r['Renter']:,.0f}</td>"
            f"<td>{r['Netto cashflow']:,.0f}</td>"
            f"<td>{r['Akk. cashflow']:,.0f}</td>"
            f"</tr>"
        )
    return "".join(out)

# --- Generer & last ned presentasjon ---
rapport_bytes = lag_presentasjon_html(note=note,
    df=df,
    kjøpesum=int(kjøpesum),
    dokumentavgift=int(kjøpskostnader),
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
    prosjekt_navn=proj_navn,
    finn_url=finn_url,
)

st.markdown("---")
st.subheader("📄 Presentasjon")
st.download_button(
    "Last ned presentasjon (HTML)",
    data=rapport_bytes,
    file_name="rapport.html",
    mime="text/html",
    use_container_width=True,
)
st.caption("Tips: Åpne HTML → Print → Lagre som PDF.")

# ---------- Lagre persist til fil ----------
if st.session_state["_dirty"]:
    _save_persist(st.session_state["persist"])
    st.session_state["_dirty"] = False
