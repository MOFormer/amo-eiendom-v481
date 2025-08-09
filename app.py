import streamlit as st
import pandas as pd

import json
from io import BytesIO
import altair as alt

# --- HJELPERE ---
def sum_namespace(prefix: str, defaults: dict, ns: int) -> int:
    s = 0
    for k in defaults:
        s += int(st.session_state.get(f"{prefix}_{k}_{ns}", 0) or 0)
    return s

def read_section_values(prefix: str, defaults: dict, ns: int) -> dict:
    """Les verdier fra aktive (namespacede) inputs i en seksjon."""
    data = {}
    for k in defaults:
        data[k] = int(st.session_state.get(f"{prefix}_{k}_{ns}", 0) or 0)
    return data

def write_section_values(prefix: str, values: dict, ns: int):
    """Skriv verdier inn i session_state for en ny namespace-runde (remount)."""
    for k, v in values.items():
        st.session_state[f"{prefix}_{k}_{ns}"] = int(v)

# --- Prosjekt-profiler pre-state ---
if "projects" not in st.session_state:
    st.session_state["projects"] = {}  # name -> dict
if "current_project_name" not in st.session_state:
    st.session_state["current_project_name"] = ""

# --- Pending load (må håndteres før UI bygges) ---
if "pending_load_profile" not in st.session_state:
    st.session_state["pending_load_profile"] = None  # dict eller None

if st.session_state["pending_load_profile"] is not None:
    p = st.session_state["pending_load_profile"]

    # Oppdater grunnfelter
    st.session_state["loaded_kjøpesum"] = p.get("kjøpesum", 0)
    st.session_state["loaded_leie"] = p.get("leie", 0)
    st.session_state["egenkapital"] = p.get("egenkapital", st.session_state.get("egenkapital", 0))
    st.session_state["rente"] = p.get("rente", st.session_state.get("rente", 5.0))
    st.session_state["løpetid"] = p.get("løpetid", st.session_state.get("løpetid", 25))
    st.session_state["avdragsfri"] = p.get("avdragsfri", st.session_state.get("avdragsfri", 0))
    st.session_state["lånetype"] = p.get("lånetype", st.session_state.get("lånetype", "Annuitetslån"))
    st.session_state["eierform"] = p.get("eierform", st.session_state.get("eierform", "Privat"))

    # Bump namespaces for å remounte inputs
    st.session_state["opp_ns"] = st.session_state.get("opp_ns", 0) + 1
    st.session_state["drift_ns"] = st.session_state.get("drift_ns", 0) + 1
    opp_ns = st.session_state["opp_ns"]
    drift_ns = st.session_state["drift_ns"]

    # Skriv inn seksjons-verdier i nye namespace-keys
    if "oppussing" in p:
        write_section_values("opp", p["oppussing"], opp_ns)
    if "drift" in p:
        write_section_values("drift", p["drift"], drift_ns)

    # Marker valgt navn
    st.session_state["current_project_name"] = p.get("navn", "")

    # Ferdig
    st.session_state["pending_load_profile"] = None

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
st.sidebar.markdown("---")
st.sidebar.subheader("📁 Prosjektprofiler")

# Navn på prosjekt
proj_name = st.sidebar.text_input("Prosjektnavn", value=st.session_state.get("current_project_name", ""))

# Lagre aktivt prosjekt til session_state
if st.sidebar.button("💾 Lagre prosjekt"):
    # Les aktive verdier
    active_proj = {
        "navn": proj_name.strip() or "Uten navn",
        "kjøpesum": kjøpesum,
        "leie": leie,
        "egenkapital": st.session_state.get("egenkapital", 0),
        "rente": st.session_state.get("rente", 5.0),
        "løpetid": st.session_state.get("løpetid", 25),
        "avdragsfri": st.session_state.get("avdragsfri", 0),
        "lånetype": st.session_state.get("lånetype", "Annuitetslån"),
        "eierform": st.session_state.get("eierform", "Privat"),
        "oppussing": read_section_values("opp", oppussing_defaults, st.session_state.get("opp_ns", 0)),
        "drift": read_section_values("drift", driftskostnader_defaults, st.session_state.get("drift_ns", 0)),
    }
    st.session_state["projects"][active_proj["navn"]] = active_proj
    st.session_state["current_project_name"] = active_proj["navn"]
    st.sidebar.success(f"Prosjekt lagret: {active_proj['navn']}")

# Velg og last prosjekt fra session_state
if st.session_state["projects"]:
    chooser = st.sidebar.selectbox(
        "Åpne prosjekt",
        options=["(Velg)"] + sorted(st.session_state["projects"].keys()),
        index=0,
        help="Velg et lagret prosjekt for å laste verdier"
    )
    if chooser != "(Velg)":
        if st.sidebar.button("📂 Last valgt prosjekt"):
            st.session_state["pending_load_profile"] = st.session_state["projects"][chooser]

        if st.sidebar.button("🗑️ Slett valgt prosjekt"):
            st.session_state["projects"].pop(chooser, None)
            if st.session_state.get("current_project_name") == chooser:
                st.session_state["current_project_name"] = ""
            st.sidebar.warning(f"Slettet: {chooser}")

# Eksporter/importer JSON
if st.session_state["projects"]:
    export_json = json.dumps(st.session_state["projects"], ensure_ascii=False, indent=2)
    st.sidebar.download_button(
        "⬇️ Last ned alle prosjekter (JSON)",
        data=export_json.encode("utf-8"),
        file_name="prosjekter.json",
        mime="application/json",
    )

uploaded = st.sidebar.file_uploader("⬆️ Importer prosjekter (JSON)", type=["json"])
if uploaded is not None:
    try:
        data = json.load(uploaded)
        if isinstance(data, dict):
            st.session_state["projects"].update(data)
            st.sidebar.success("Prosjekter importert.")
        else:
            st.sidebar.error("Ugyldig JSON-format. Forventet et objekt/dict.")
    except Exception as e:
        st.sidebar.error(f"Kunne ikke lese JSON: {e}")

st.sidebar.header("🧾 Eiendomsinfo")
kjøpesum = st.sidebar.number_input("Kjøpesum", value=4_000_000, step=100_000)
leie = st.sidebar.number_input("Leieinntekter / mnd", value=22_000)
kjøpskostnader = kjøpesum * 0.025  # 2.5 % kjøpsomkostninger

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

# Tittel-sum må beregnes etter pre-reset
opp_title_total = sum_namespace("opp", oppussing_defaults, st.session_state["opp_ns"])
with st.sidebar.expander(f"🔨 Oppussing: {opp_title_total:,} kr", expanded=True):
    # Knappen settes inni boksen, men ber bare om reset via flagg
    st.button(
        "Tilbakestill oppussing",
        key="btn_reset_opp",
        on_click=lambda: st.session_state.__setitem__("opp_reset_request", True),
    )

    ns = st.session_state["opp_ns"]
    oppussing_total = 0
    for key, default in oppussing_defaults.items():
        wkey = f"opp_{key}_{ns}"
        # første runde: default, senere runder: behold skriverens verdi hvis finnes, ellers 0
        startverdi = st.session_state.get(wkey, default if ns == 0 else 0)
        val = st.number_input(key.capitalize(), value=startverdi, key=wkey, step=1000, format="%d")
        oppussing_total += val

    st.markdown(f"**Totalt: {int(oppussing_total):,} kr**")

st.markdown("### 📤 Eksporter kontantstrøm")
# CSV
csv_bytes = df.to_csv(index=False).encode("utf-8")
st.download_button(
    "Last ned CSV",
    data=csv_bytes,
    file_name="kontantstrom.csv",
    mime="text/csv",
)

# Excel
buffer = BytesIO()
with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
    df.to_excel(writer, index=False, sheet_name="Kontantstrøm")
    # (valgfritt) auto-width
    for i, col in enumerate(df.columns):
        width = max(12, min(40, int(df[col].astype(str).str.len().max() or 12)))
        writer.sheets["Kontantstrøm"].set_column(i, i, width)
buffer.seek(0)
st.download_button(
    "Last ned Excel",
    data=buffer,
    file_name="kontantstrom.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)


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
with st.sidebar.expander(f"💡 Driftskostnader: {drift_title_total:,} kr", expanded=True):
    st.button(
        "Tilbakestill driftskostnader",
        key="btn_reset_drift",
        on_click=lambda: st.session_state.__setitem__("drift_reset_request", True),
    )

    ns = st.session_state["drift_ns"]
    drift_total = 0
    for key, default in driftskostnader_defaults.items():
        wkey = f"drift_{key}_{ns}"
        startverdi = st.session_state.get(wkey, default if ns == 0 else 0)
        val = st.number_input(key.capitalize(), value=startverdi, key=wkey, step=1000, format="%d")
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

with st.sidebar.expander(f"🏦 Lån: {int(st.session_state['lån']):,} kr", expanded=True):
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

# Altair: splitt i to lag – positive og negative
df_plot = df[["Måned", "Netto cashflow", "Akk. cashflow"]].copy()
df_plot.rename(columns={"Måned": "Maaned", "Netto cashflow": "Netto", "Akk. cashflow": "Akk"}, inplace=True)

pos = alt.Chart(df_plot).transform_filter("datum.Netto >= 0").mark_line().encode(
    x=alt.X("Maaned:Q", title="Måned"),
    y=alt.Y("Netto:Q", title="Netto cashflow"),
    color=alt.value("#2e7d32"),  # grønn
    tooltip=["Maaned","Netto"]
)

neg = alt.Chart(df_plot).transform_filter("datum.Netto < 0").mark_line().encode(
    x=alt.X("Maaned:Q"),
    y=alt.Y("Netto:Q"),
    color=alt.value("#c62828"),  # rød
    tooltip=["Maaned","Netto"]
)

akk = alt.Chart(df_plot).mark_line().encode(
    x=alt.X("Maaned:Q"),
    y=alt.Y("Akk:Q", title="Akk. cashflow"),
    color=alt.value("#1565c0"),  # blå
    tooltip=["Maaned","Akk"]
)

st.altair_chart((pos + neg).properties(height=300, width="container"), use_container_width=True)
st.altair_chart(akk.properties(height=300, width="container"), use_container_width=True)
