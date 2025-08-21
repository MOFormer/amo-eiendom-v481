import streamlit as st
import pandas as pd
import json
from pathlib import Path
import base64

# =========================
#   Persist / Autosave
# =========================
PERSIST_PATH = Path("autosave.json")
PROFILES_PATH = Path("profiles.json")

def _load_json(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def _save_json(path: Path, data: dict):
    try:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

# Init session_state
if "persist" not in st.session_state:
    st.session_state["persist"] = _load_json(PERSIST_PATH)
if "_dirty" not in st.session_state:
    st.session_state["_dirty"] = False
if "profiles" not in st.session_state:
    st.session_state["profiles"] = _load_json(PROFILES_PATH)
if "pending_profile_name" not in st.session_state:
    st.session_state["pending_profile_name"] = ""

def mark_dirty():
    st.session_state["_dirty"] = True

# =========================
#   App Config
# =========================
st.set_page_config(layout="wide")
st.title("AMO Eiendomskalkulator")

# =========================
#   Helpers
# =========================
def _img_bytes_to_b64(img_bytes: bytes) -> str:
    import base64 as _b64
    return _b64.b64encode(img_bytes).decode("utf-8")

def beregn_lån(lån, rente, løpetid, avdragsfri, lånetype, leie, drift_mnd, eierform):
    """Returnerer df med månedsrader + akkumulert netto cashflow."""
    import pandas as _pd
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

        netto = float(leie) - float(drift_mnd) - termin
        if eierform == "AS" and netto > 0:
            netto *= (1 - 0.375)

        akk += netto
        restgjeld.append(saldo)
        avdrag.append(avdrag_mnd)
        renter_liste.append(rente_mnd)
        netto_cf.append(netto)
        akk_cf.append(akk)

    return _pd.DataFrame({
        "Måned": list(range(1, n + 1)),
        "Restgjeld": restgjeld,
        "Avdrag": avdrag,
        "Renter": renter_liste,
        "Netto cashflow": netto_cf,
        "Akk. cashflow": akk_cf
    }), akk

def _first_month_kpis(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"termin": 0.0, "netto": 0.0}
    r = df.iloc[0]
    return {"termin": float(r["Renter"] + r["Avdrag"]), "netto": float(r["Netto cashflow"])}

def _break_even_month(df: pd.DataFrame):
    if df.empty:
        return None
    mask = df["Akk. cashflow"] >= 0
    if not mask.any():
        return None
    idx = mask.idxmax()
    return int(df.iloc[idx]["Måned"])

def _skattefradrag_estimat(df: pd.DataFrame, drift_mnd_total: int) -> dict:
    """Forenklet: Renter år 1 + driftskostnader år = fradrag (estimat)."""
    renter_aar1 = float(df["Renter"].head(12).sum()) if not df.empty else 0.0
    drift_aar = float(drift_mnd_total) * 12.0
    fradrag_sum = renter_aar1 + drift_aar
    return {"renter_aar1": renter_aar1, "drift_aar": drift_aar, "fradrag_aar1_sum": fradrag_sum}

def _verdistigning_liste(startverdi: float, antall_ar: int, rate: float = 0.025) -> list[dict]:
    """Returnerer liste med {'År': i, 'Verdi': verdi} for år 0..N."""
    out = []
    verdi = float(startverdi)
    out.append({"År": 0, "Verdi": round(verdi)})
    for i in range(1, antall_ar + 1):
        verdi *= (1.0 + rate)
        out.append({"År": i, "Verdi": round(verdi)})
    return out

# ---- NYTT: Rom-normalisering (fikser 'soverom' → 'rom') ----
def _migrate_soverom_keys():
    """Hvis gamle nøkler 'soverom_i' finnes og 'rom_i' ikke finnes,
    kopierer vi verdiene over til 'rom_i' for bakoverkompatibilitet."""
    rooms = st.session_state["persist"].setdefault("rooms_leie", {})
    has_rom = any(k.startswith("rom_") for k in rooms)
    has_soverom = any(k.startswith("soverom_") for k in rooms)
    if not has_rom and has_soverom:
        for k, v in list(rooms.items()):
            if k.startswith("soverom_"):
                try:
                    idx = int(k.split("_")[1])
                    rooms[f"rom_{idx}"] = int(v)
                except Exception:
                    pass
        mark_dirty()

def _normalized_room_pairs(rooms_dict: dict, antall_rom: int) -> list[tuple[int, int]]:
    """Returnerer [(1, beløp1), (2, beløp2), ...] uavhengig av om nøkler heter rom_i eller soverom_i."""
    out = []
    for i in range(1, int(antall_rom) + 1):
        v = None
        for key in (f"rom_{i}", f"soverom_{i}", f"room_{i}"):
            if key in rooms_dict:
                try:
                    v = int(rooms_dict[key])
                except Exception:
                    v = 0
                break
        out.append((i, v if v is not None else 0))
    return out

# ================ Pending LOAD ================
if st.session_state["pending_profile_name"]:
    sel = st.session_state["pending_profile_name"]
    p = st.session_state["profiles"].get(sel, {})

    # Persist (grunninfo)
    st.session_state["persist"]["prosjekt_navn"] = p.get("prosjekt_navn", sel)
    st.session_state["persist"]["finn_url"]      = p.get("finn_url", "")
    st.session_state["persist"]["note"]          = p.get("note", "")
    st.session_state["persist"]["cover_url"]     = p.get("cover_url", "")
    if p.get("cover_b64"):
        st.session_state["persist"]["cover_b64"] = p.get("cover_b64", "")

    # Kjøp/inntekter
    st.session_state["persist"]["kjøpesum"]   = p.get("kjøpesum", 0)
    st.session_state["persist"]["leie"]       = p.get("leie", 0)
    st.session_state["persist"]["use_rooms_total"] = p.get("use_rooms_total", False)
    st.session_state["persist"]["rooms_leie"] = p.get("rooms_leie", {})
    st.session_state["persist"]["antall_rom"] = p.get("antall_rom", 0)

    # Kostnader
    st.session_state["persist"]["opp"]       = p.get("oppussing", {})
    st.session_state["persist"]["drift_mnd"] = p.get("drift_mnd", {})

    # Lån
    st.session_state["egenkapital"] = p.get("egenkapital", 300000)
    st.session_state["rente"]       = p.get("rente", 5.0)
    st.session_state["løpetid"]     = p.get("løpetid", 25)
    st.session_state["avdragsfri"]  = p.get("avdragsfri", 2)
    st.session_state["lånetype"]    = p.get("lånetype", "Annuitetslån")
    st.session_state["eierform"]    = p.get("eierform", "Privat")

    # Oppdater UI felter som bruker faste keys
    st.session_state["prosjektnavn_input"] = st.session_state["persist"]["prosjekt_navn"]
    st.session_state["finn_url_input"]     = st.session_state["persist"]["finn_url"]

    st.session_state["pending_profile_name"] = ""
    st.rerun()

# ========================= Sidebar: Grunninfo =========================
st.sidebar.header("🧾 Eiendomsinfo")

proj_navn = st.sidebar.text_input(
    "Prosjektnavn",
    key="prosjektnavn_input",
    value=st.session_state["persist"].get("prosjekt_navn", "Eiendomsprosjekt"),
    on_change=mark_dirty,
)
st.session_state["persist"]["prosjekt_navn"] = proj_navn

finn_url = st.sidebar.text_input(
    "FINN-annonse (URL)",
    key="finn_url_input",
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

# Forsidebilde
st.sidebar.markdown("**Forsidebilde** (vises i presentasjonen)")
cover_url = st.sidebar.text_input(
    "Bilde-URL (valgfritt)",
    value=st.session_state["persist"].get("cover_url", ""),
    on_change=mark_dirty,
    placeholder="https://..."
)
if cover_url and not cover_url.startswith(("http://", "https://")):
    cover_url = "https://" + cover_url
st.session_state["persist"]["cover_url"] = cover_url

uploaded_cover = st.sidebar.file_uploader("…eller last opp JPG/PNG", type=["jpg", "jpeg", "png"])
if uploaded_cover is not None:
    cover_b64 = _img_bytes_to_b64(uploaded_cover.read())
    st.session_state["persist"]["cover_b64"] = cover_b64
    mark_dirty()
else:
    cover_b64 = st.session_state["persist"].get("cover_b64", "")

# ========================= Kjøp & Inntekter =========================
kjøpesum = st.sidebar.number_input(
    "Kjøpesum (kr)",
    value=int(st.session_state["persist"].get("kjøpesum", 4_000_000)),
    step=100_000,
    on_change=mark_dirty,
)
st.session_state["persist"]["kjøpesum"] = int(kjøpesum)
dokumentavgift = int(kjøpesum * 0.025)

# ========================= Expanders =========================
# --- ROM & LEIE PR. ROM ---
with st.sidebar.expander("🏠 Rom & leie pr. rom", expanded=False):
    antall_rom = st.number_input(
        "Antall rom",
        min_value=0,
        step=1,
        value=int(st.session_state["persist"].get("antall_rom", 0)),
        on_change=mark_dirty,
        key="rooms_count",
    )
    st.session_state["persist"]["antall_rom"] = int(antall_rom)

    # migrer ev. gamle 'soverom_*' til 'rom_*'
    _migrate_soverom_keys()

    rooms_key = "rooms_leie"
    st.session_state["persist"].setdefault(rooms_key, {})
    # vis og lagre 'rom_i' i UI
    sum_rom = 0
    for i in range(int(antall_rom)):
        rk = f"rom_{i+1}"
        default_val = int(st.session_state["persist"][rooms_key].get(rk, 0))
        val = st.number_input(f"Rom {i+1} (kr/mnd)", min_value=0, step=500, value=default_val, key=f"room_input_{i+1}")
        if st.session_state["persist"][rooms_key].get(rk) != int(val):
            st.session_state["persist"][rooms_key][rk] = int(val)
            mark_dirty()
        sum_rom += int(val)

    use_rooms_total = st.checkbox(
        "Bruk sum av rom som total leie",
        value=bool(st.session_state["persist"].get("use_rooms_total", False)),
        key="use_rooms_total_chk"
    )
    st.session_state["persist"]["use_rooms_total"] = use_rooms_total

    leie_input = st.number_input(
        "Leieinntekter – total (kr/mnd)",
        value=int(st.session_state["persist"].get("leie", 22_000)),
        step=1_000,
        on_change=mark_dirty,
        key="leie_total_input",
    )
    st.session_state["persist"]["leie"] = int(leie_input)

# Leie som brukes i videre beregning
leie = int(sum_rom) if st.session_state["persist"].get("use_rooms_total", False) else int(st.session_state["persist"].get("leie", 0))

# --- OPPUSSING ---
with st.sidebar.expander("🔨 Oppussing", expanded=False):
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
    st.session_state["persist"].setdefault("opp", oppussing_defaults.copy())

    def _reset_opp_to_zero():
        st.session_state["persist"]["opp"] = {k: 0 for k in oppussing_defaults}
        mark_dirty()
        st.rerun()

    def _reset_opp_to_defaults():
        st.session_state["persist"]["opp"] = oppussing_defaults.copy()
        mark_dirty()
        st.rerun()

    c1, c2 = st.columns(2)
    c1.button("Nullstill", on_click=_reset_opp_to_zero, key="btn_opp_zero")
    c2.button("Til standard", on_click=_reset_opp_to_defaults, key="btn_opp_defaults")

    oppussing_total = 0
    for key, default in oppussing_defaults.items():
        saved_val = int(st.session_state["persist"]["opp"].get(key, default))
        val = st.number_input(key.capitalize(), value=saved_val, step=1000, format="%d", key=f"opp_{key}")
        val = int(val)
        if st.session_state["persist"]["opp"].get(key) != val:
            st.session_state["persist"]["opp"][key] = val
            mark_dirty()
        oppussing_total += val
    st.caption(f"**Sum oppussing:** {oppussing_total:,} kr")

# --- DRIFTSKOSTNADER (MND) ---
with st.sidebar.expander("💡 Driftskostnader (per måned)", expanded=False):
    driftskostnader_defaults = {
        "felleskostnader": 0,
        "kommunale avgifter": 0,
        "strøm": 0,
        "internett": 0,
        "forsikring": 0,
        "vedlikehold": 0,
        "husleie (kostnad)": 0,
    }
    st.session_state["persist"].setdefault("drift_mnd", driftskostnader_defaults.copy())

    def _reset_drift_to_zero():
        st.session_state["persist"]["drift_mnd"] = {k: 0 for k in driftskostnader_defaults}
        mark_dirty()
        st.rerun()

    def _reset_drift_to_defaults():
        st.session_state["persist"]["drift_mnd"] = driftskostnader_defaults.copy()
        mark_dirty()
        st.rerun()

    d1, d2 = st.columns(2)
    d1.button("Nullstill", on_click=_reset_drift_to_zero, key="btn_drift_zero")
    d2.button("Til standard", on_click=_reset_drift_to_defaults, key="btn_drift_defaults")

    drift_mnd_total = 0
    for key, default in driftskostnader_defaults.items():
        saved_val = int(st.session_state["persist"]["drift_mnd"].get(key, default))
        val = st.number_input(key.capitalize(), value=saved_val, step=200, format="%d", key=f"drift_{key}")
        val = int(val)
        if st.session_state["persist"]["drift_mnd"].get(key) != val:
            st.session_state["persist"]["drift_mnd"][key] = val
            mark_dirty()
        drift_mnd_total += val
    st.caption(f"**Sum drift / mnd:** {drift_mnd_total:,} kr")

# --- LÅN ---
with st.sidebar.expander("🏦 Lån", expanded=False):
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

    st.session_state["egenkapital"] = st.number_input("Egenkapital (kr)", value=int(st.session_state["egenkapital"]), step=10000)
    st.session_state["rente"] = st.number_input("Rente (%)", value=float(st.session_state["rente"]), step=0.1)
    st.session_state["løpetid"] = st.number_input("Løpetid (år)", value=int(st.session_state["løpetid"]), step=1, min_value=1)
    st.session_state["avdragsfri"] = st.number_input("Avdragsfri (år)", value=int(st.session_state["avdragsfri"]), step=1, min_value=0)
    st.session_state["lånetype"] = st.selectbox("Lånetype", ["Annuitetslån", "Serielån"], index=["Annuitetslån", "Serielån"].index(st.session_state["lånetype"]))
    st.session_state["eierform"] = st.radio("Eierform", ["Privat", "AS"], index=["Privat", "AS"].index(st.session_state["eierform"]))

    for k in lån_defaults:
        if st.session_state["persist"].get(k) != st.session_state[k]:
            st.session_state["persist"][k] = st.session_state[k]
            mark_dirty()

# ========================= Beregninger =========================
total_investering = int(kjøpesum + dokumentavgift + oppussing_total)
lånebeløp = max(total_investering - int(st.session_state["egenkapital"]), 0)
st.session_state["lån"] = lånebeløp

df, _akk = beregn_lån(
    lån=int(st.session_state["lån"]),
    rente=float(st.session_state["rente"]),
    løpetid=int(st.session_state["løpetid"]),
    avdragsfri=int(st.session_state["avdragsfri"]),
    lånetype=st.session_state["lånetype"],
    leie=int(leie),
    drift_mnd=int(drift_mnd_total),
    eierform=st.session_state["eierform"]
)

kpis_1 = _first_month_kpis(df)
breakeven_mnd = _break_even_month(df)
skatt = _skattefradrag_estimat(df, drift_mnd_total)

# Verdistigning
startverdi = float(kjøpesum + oppussing_total)
verdistigning = _verdistigning_liste(startverdi, int(st.session_state["løpetid"]), rate=0.025)
verdi_df = pd.DataFrame(verdistigning)

# ========================= Profiler =========================
st.sidebar.markdown("---")
st.sidebar.subheader("📁 Profiler")

profile_name = st.sidebar.text_input(
    "Profilnavn (for lagring)",
    key="profile_name_input",
    value=st.session_state["persist"].get("prosjekt_navn", "Eiendomsprosjekt"),
)

def _current_profile_payload() -> dict:
    return {
        "prosjekt_navn": st.session_state["persist"].get("prosjekt_navn", profile_name),
        "finn_url":      st.session_state["persist"].get("finn_url", ""),
        "note":          st.session_state["persist"].get("note", ""),
        "cover_url":     st.session_state["persist"].get("cover_url", ""),
        "cover_b64":     st.session_state["persist"].get("cover_b64", ""),
        "kjøpesum":      int(kjøpesum),
        "leie":          int(st.session_state["persist"].get("leie", 0)),
        "use_rooms_total": bool(st.session_state["persist"].get("use_rooms_total", False)),
        "rooms_leie":    st.session_state["persist"].get("rooms_leie", {}),
        "antall_rom":    int(st.session_state["persist"].get("antall_rom", 0)),
        "oppussing":     st.session_state["persist"].get("opp", {}),
        "drift_mnd":     st.session_state["persist"].get("drift_mnd", {}),
        "egenkapital":   int(st.session_state["egenkapital"]),
        "rente":         float(st.session_state["rente"]),
        "løpetid":       int(st.session_state["løpetid"]),
        "avdragsfri":    int(st.session_state["avdragsfri"]),
        "lånetype":      st.session_state["lånetype"],
        "eierform":      st.session_state["eierform"],
    }

def _save_profiles_now():
    _save_json(PROFILES_PATH, st.session_state["profiles"])

if st.sidebar.button("💾 Lagre profil", key="btn_save_profile"):
    name = (profile_name or "").strip() or "Uten navn"
    st.session_state["profiles"][name] = _current_profile_payload()
    _save_profiles_now()
    st.sidebar.success(f"Lagret: {name}")

existing = ["(Velg)"] + sorted(st.session_state["profiles"].keys())
sel = st.sidebar.selectbox("Åpne / Slett profil", options=existing, index=0, key="profile_select")

def _queue_load_profile(name: str):
    st.session_state["pending_profile_name"] = name

def _delete_selected(name: str):
    st.session_state["profiles"].pop(name, None)
    _save_profiles_now()
    st.sidebar.warning(f"Slettet: {name}")

if sel != "(Velg)":
    st.sidebar.button("📂 Last profil", key="btn_load_profile", on_click=_queue_load_profile, args=(sel,))
    st.sidebar.button("🗑️ Slett profil", key="btn_delete_profile", on_click=_delete_selected, args=(sel,))

# ========================= Hovedinnhold =========================
st.markdown("---")
col1, col2 = st.columns([1, 1.4])

with col1:
    st.subheader("✨ Resultater")
    brutto_yield = (leie * 12 / total_investering) * 100 if total_investering else 0
    netto_yield = ((leie * 12 - drift_mnd_total * 12) / total_investering) * 100 if total_investering else 0
    st.metric("Total investering", f"{int(total_investering):,} kr")
    st.metric("Brutto yield", f"{brutto_yield:.2f} %")
    st.metric("Netto yield", f"{netto_yield:.2f} %")
    st.metric("Lån", f"{int(st.session_state['lån']):,} kr")
    st.metric("Termin 1. mnd (ca.)", f"{kpis_1['termin']:,.0f} kr")
    st.metric("Netto 1. mnd (ca.)", f"{kpis_1['netto']:,.0f} kr")
    st.metric("Break-even måned", f"{breakeven_mnd if breakeven_mnd else '—'}")

    st.subheader("Skattefradrag (estimat)")
    st.write(
        f"""
- **Renteutgifter år 1:** {skatt['renter_aar1']:,.0f} kr  
- **Driftskostnader pr. år:** {skatt['drift_aar']:,.0f} kr  
- **Sum fradragsutgifter (år 1, forenklet):** **{skatt['fradrag_aar1_sum']:,.0f} kr**
"""
    )
    st.caption("Forenklet oversikt. Vedlikehold er normalt fradragsberettiget, mens påkostning ikke er det.")

    st.subheader("Kontantstrøm (første 60 måneder)")
    st.dataframe(df.head(60), use_container_width=True, height=420)

with col2:
    st.subheader("Oppsummering")
    st.write(
        f"""
- **Leie som brukes:** {leie:,.0f} kr/mnd  
- **Driftskostnader:** {drift_mnd_total:,.0f} kr/mnd  
- **Avdragsfri:** {int(st.session_state['avdragsfri'])} år  
- **Løpetid:** {int(st.session_state['løpetid'])} år ({st.session_state['lånetype']})  
- **Eierform:** {st.session_state['eierform']}
"""
    )

    # Romtabell i UI (støtter gamle 'soverom_*' nøkler)
    rooms_dict = st.session_state["persist"].get("rooms_leie", {})
    antall_rom_ui = int(st.session_state["persist"].get("antall_rom", 0))
    if antall_rom_ui > 0:
        st.subheader("Rom & leie pr. rom")
        pairs = _normalized_room_pairs(rooms_dict, antall_rom_ui)  # [(i, beløp)]
        rows = [{"Rom": idx, "Leie (kr/mnd)": beløp} for idx, beløp in pairs]
        if rows:
            df_rooms = pd.DataFrame(rows)
            df_rooms.loc["Sum"] = ["", df_rooms["Leie (kr/mnd)"].sum()]
            st.table(df_rooms)

    st.subheader("Verdiutvikling (2,5 % årlig)")
    st.dataframe(verdi_df, use_container_width=True, height=360)

# ========================= Presentasjon (HTML) =========================
def lag_presentasjon_html(
    df: pd.DataFrame,
    prosjekt_navn: str,
    finn_url: str,
    note: str,
    cover_url: str = "",
    cover_b64: str = "",
    kjøpesum: int = 0,
    dokumentavgift: int = 0,
    oppussing_total: int = 0,
    drift_mnd: int = 0,
    total_investering: int = 0,
    leie: int = 0,
    rente: float = 0.0,
    løpetid: int = 0,
    avdragsfri: int = 0,
    lånetype: str = "Annuitetslån",
    eierform: str = "Privat",
    egenkapital: int = 0,
    # Rom
    antall_rom: int = 0,
    rom_renter: dict | None = None,
    # Skatt og verdi
    skatt: dict | None = None,
    verdi_tabell: list[dict] | None = None,
) -> bytes:
    def _safe(s: str) -> str:
        return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # Klikkbar lenke + rå-URL fallback
    finn_html = ""
    if finn_url:
        safe_url = _safe(finn_url)
        finn_html = f'''
          <p>
            <a href="{safe_url}" target="_blank" rel="noopener noreferrer" class="btn" style="pointer-events:auto; cursor:pointer;">
              🔗 Åpne FINN-annonsen
            </a>
          </p>
          <p class="muted" style="margin-top:-6px;">
            Direkte lenke: <span style="text-decoration:underline; color:#0b63ce;">{safe_url}</span>
          </p>
        '''

    # Forsidebilde
    cover_html = ""
    if cover_b64:
        cover_html = f'''
          <div class="hero-img">
            <img src="data:image/png;base64,{cover_b64}" alt="Forsidebilde" />
          </div>'''
    elif cover_url:
        cover_html = f'''
          <div class="hero-img">
            <img src="{_safe(cover_url)}" alt="Forsidebilde" />
          </div>'''

    # Rom-detaljer (alltid "Rom X")
    pairs = _normalized_room_pairs(rom_renter or {}, antall_rom)  # [(i, beløp)]
    rom_sum = sum(b for _, b in pairs)
    leie_kilde = "Sum av rom" if rom_sum == leie and antall_rom > 0 else "Manuelt totalt"
    snitt_pr_rom = int(leie / antall_rom) if antall_rom > 0 else 0

    # KPI-er
    brutto_yield = (leie * 12 / total_investering) * 100 if total_investering else 0
    netto_yield  = ((leie * 12 - drift_mnd * 12) / total_investering) * 100 if total_investering else 0

    # Kontantstrøm (første 24 mnd)
    vis_mnd = min(24, len(df))
    cash_rows = []
    for i in range(vis_mnd):
        r = df.iloc[i]
        cash_rows.append(
            f"<tr>"
            f"<td>{int(r['Måned'])}</td>"
            f"<td>{r['Restgjeld']:,.0f}</td>"
            f"<td>{r['Avdrag']:,.0f}</td>"
            f"<td>{r['Renter']:,.0f}</td>"
            f"<td>{r['Netto cashflow']:,.0f}</td>"
            f"<td>{r['Akk. cashflow']:,.0f}</td>"
            f"</tr>"
        )
    cash_html = "".join(cash_rows)

    # Oppussingstabell
    opp_rows = ""
    if oppussing_total:
        opp_dict = st.session_state['persist'].get('opp', {}) or {}
        opp_rows = (
            "<table class='tight'><thead><tr><th>Tiltak</th><th>Beløp</th></tr></thead><tbody>"
            + "".join(f"<tr><td>{_safe(k.capitalize())}</td><td>{int(v):,} kr</td></tr>"
                      for k, v in opp_dict.items())
            + f"<tr class='total'><td>Sum</td><td>{oppussing_total:,.0f} kr</td></tr>"
            + "</tbody></table>"
        )

    # Drift pr mnd tabell
    drift_rows = ""
    if drift_mnd:
        drift_dict = st.session_state["persist"].get("drift_mnd", {}) or {}
        drift_rows = (
            "<table class='tight'><thead><tr><th>Post</th><th>Kr / mnd</th></tr></thead><tbody>"
            + "".join(f"<tr><td>{_safe(k.capitalize())}</td><td>{int(v):,} kr</td></tr>"
                      for k, v in drift_dict.items())
            + f"<tr class='total'><td>Sum / mnd</td><td>{drift_mnd:,.0f} kr</td></tr>"
            + "</tbody></table>"
        )

    # Rom-tabell (etikett alltid "Rom i")
    rom_table = ""
    if antall_rom > 0:
        rom_table = (
            "<table class='tight'><thead><tr><th>Rom</th><th>Leie / mnd</th></tr></thead><tbody>"
            + "".join(f"<tr><td>Rom {idx}</td><td>{int(b):,} kr</td></tr>" for idx, b in pairs)
            + f"<tr class='total'><td>Sum</td><td>{rom_sum:,} kr</td></tr>"
            + "</tbody></table>"
        )

    # Skattefradrag
    skatt_html = ""
    if skatt:
        skatt_html = f"""
        <table class="tight">
          <thead><tr><th>Post</th><th>Beløp (kr)</th></tr></thead>
          <tbody>
            <tr><td>Renteutgifter år 1</td><td>{skatt['renter_aar1']:,.0f}</td></tr>
            <tr><td>Driftskostnader pr. år</td><td>{skatt['drift_aar']:,.0f}</td></tr>
            <tr class="total"><td>Sum fradragsutgifter (år 1, forenklet)</td><td>{skatt['fradrag_aar1_sum']:,.0f}</td></tr>
          </tbody>
        </table>
        <p class="muted">Forenklet oversikt. Skatteregler kan variere (vedlikehold vs. påkostning m.m.).</p>
        """

    # Verdiutvikling
    verdi_html = ""
    if verdi_tabell:
        rows = "".join(f"<tr><td>{int(r['År'])}</td><td>{int(r['Verdi']):,} kr</td></tr>" for r in verdi_tabell)
        verdi_html = f"""
        <table class="tight">
          <thead><tr><th>År</th><th>Estimert verdi (2,5 % årlig)</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>
        """

    html = f"""
<!DOCTYPE html>
<html lang="no">
<head>
<meta charset="utf-8" />
<title>{_safe(prosjekt_navn)} – Presentasjon</title>
<style>
  :root {{
    --bg:#fafafa; --card:#ffffff; --text:#111; --muted:#666; --border:#eaeaea; --brand:#0b63ce;
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 24px; font-family: -apple-system, BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; color: var(--text); background: var(--bg); }}
  h1 {{ font-size: 28px; margin: 0 0 10px; }}
  h2 {{ font-size: 20px; margin: 0 0 12px; }}
  .muted {{ color: var(--muted); }}
  .btn {{
    display:inline-block; padding:8px 12px; border:1px solid var(--brand); color: var(--brand);
    border-radius:10px; text-decoration:none; font-weight:600;
  }}
  .hero {{ display:grid; grid-template-columns: 1fr auto; gap: 16px; align-items:center; }}
  .hero-img img {{
    max-width: 360px; width: 100%;
    border: 1px solid var(--border); border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,.06);
  }}
  .kpi {{
    margin-top: 12px;
    display:grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 12px;
  }}
  .card {{
    background: var(--card); border:1px solid var(--border); border-radius: 14px;
    padding: 14px; box-shadow: 0 1px 6px rgba(0,0,0,.04);
  }}
  .kpi .card .label {{ font-size:12px; color:var(--muted); margin-bottom:6px; }}
  .kpi .card .value {{ font-size:16px; font-weight:700; }}
  .split {{ display:grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
  table {{ width:100%; border-collapse: collapse; font-size: 12px; }}
  td, th {{ padding: 6px 8px; border-bottom:1px solid var(--border); text-align:right; }}
  th:first-child, td:first-child {{ text-align:left; }}
  table.tight td, table.tight th {{ padding: 6px 6px; }}
  tr.total td {{ font-weight: 700; }}
  .badge {{
    display:inline-block; padding:4px 8px; border-radius:999px;
    background:#eef6ff; color: var(--brand); font-size:12px; font-weight:700;
  }}
  .spacer {{ height: 8px; }}
  @media print {{ a[href]::after {{ content:" (" attr(href) ")"; font-size:11px; color:#555; }} }}
</style>
</head>
<body>

<div class="hero">
  <div>
    <h1>{_safe(prosjekt_navn)}</h1>
    <p class="muted">Generert fra AMO Eiendomskalkulator</p>
    {finn_html}
  </div>
  {cover_html}
</div>

<div class="kpi">
  <div class="card"><div class="label">Kjøpesum</div><div class="value">{kjøpesum:,.0f} kr</div></div>
  <div class="card"><div class="label">Dokumentavgift</div><div class="value">{dokumentavgift:,.0f} kr</div></div>
  <div class="card"><div class="label">Oppussing</div><div class="value">{oppussing_total:,.0f} kr</div></div>

  <div class="card"><div class="label">Drift / mnd</div><div class="value">{drift_mnd:,.0f} kr</div></div>
  <div class="card"><div class="label">Total investering</div><div class="value">{total_investering:,.0f} kr</div></div>
  <div class="card"><div class="label">Leie / mnd</div><div class="value">{leie:,.0f} kr</div></div>

  <div class="card"><div class="label">Egenkapital</div><div class="value">{egenkapital:,.0f} kr</div></div>
  <div class="card"><div class="label">Rente</div><div class="value">{rente:.2f} %</div></div>
  <div class="card"><div class="label">Yield (brutto / netto)</div><div class="value">{(leie*12/total_investering*100 if total_investering else 0):.2f}% / {((leie*12 - drift_mnd*12)/total_investering*100 if total_investering else 0):.2f}%</div></div>

  <div class="card"><div class="label">Antall rom</div><div class="value">{antall_rom}</div></div>
  <div class="card"><div class="label">Snitt pr. rom</div><div class="value">{snitt_pr_rom:,.0f} kr</div></div>
  <div class="card"><div class="label">Leie-kilde</div><div class="value"><span class="badge">{_safe(leie_kilde)}</span></div></div>
</div>

<div class="spacer"></div>

{"<div class='card'><h2>Notater</h2><p>" + _safe(note).replace("\\n","<br>") + "</p></div>" if note else ""}

<div class="spacer"></div>

<div class="split">
  <div class="card">
    <h2>Oppussing (engang)</h2>
    {opp_rows if opp_rows else "<p class='muted'>Ingen oppussingskostnader registrert.</p>"}
  </div>
  <div class="card">
    <h2>Drift (per måned)</h2>
    {drift_rows if drift_rows else "<p class='muted'>Ingen driftskostnader registrert.</p>"}
  </div>
</div>

<div class="spacer"></div>

<div class="card">
  <h2>Rom og leie</h2>
  {rom_table if rom_table else "<p class='muted'>Ingen rom spesifisert.</p>"}
</div>

<div class="spacer"></div>

<div class="split">
  <div class="card">
    <h2>Skattefradrag (estimat)</h2>
    {skatt_html if skatt_html else "<p class='muted'>Ingen beregning tilgjengelig.</p>"}
  </div>
  <div class="card">
    <h2>Verdiutvikling (2,5 % årlig)</h2>
    {verdi_html if verdi_html else "<p class='muted'>Ingen beregning tilgjengelig.</p>"}
  </div>
</div>

<div class="spacer"></div>

<div class="card">
  <h2>Kontantstrøm – første 24 måneder</h2>
  <table>
    <thead>
      <tr>
        <th>Mnd</th><th>Restgjeld</th><th>Avdrag</th><th>Renter</th><th>Netto</th><th>Akk.</th>
      </tr>
    </thead>
    <tbody>
      {cash_html}
    </tbody>
  </table>
  <p class="muted">Full tidsserie kan eksporteres fra appen.</p>
</div>

</body>
</html>
"""
    return html.encode("utf-8")

rapport_bytes = lag_presentasjon_html(
    df=df,
    prosjekt_navn=proj_navn,
    finn_url=finn_url,
    note=note,
    cover_url=st.session_state["persist"].get("cover_url", ""),
    cover_b64=st.session_state["persist"].get("cover_b64", ""),
    kjøpesum=int(kjøpesum),
    dokumentavgift=int(dokumentavgift),
    oppussing_total=int(oppussing_total),
    drift_mnd=int(drift_mnd_total),
    total_investering=int(total_investering),
    leie=int(leie),
    rente=float(st.session_state["rente"]),
    løpetid=int(st.session_state["løpetid"]),
    avdragsfri=int(st.session_state["avdragsfri"]),
    lånetype=st.session_state["lånetype"],
    eierform=st.session_state["eierform"],
    egenkapital=int(st.session_state["egenkapital"]),
    antall_rom=int(st.session_state["persist"].get("antall_rom", 0)),
    rom_renter=st.session_state["persist"].get("rooms_leie", {}),
    skatt=skatt,
    verdi_tabell=verdistigning,
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
st.caption("Åpne HTML-filen i nettleser → Skriv ut → Lagre som PDF. (Lenker og rå-URL bevares som klikkbare.)")

# ========================= Autosave persist =========================
if st.session_state["_dirty"]:
    _save_json(PERSIST_PATH, st.session_state["persist"])
    st.session_state["_dirty"] = False
