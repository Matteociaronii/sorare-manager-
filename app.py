import streamlit as st
import requests
import pandas as pd
import numpy as np

# ==========================================
# CONFIGURAZIONE PAGINA
# ==========================================
st.set_page_config(
    page_title="Sorare Pro Hub 2026/27",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_URL = "https://api.sorare.com/graphql"
IN_SEASON_YEAR = 2026

DOMESTIC_LEAGUES = {
    "serie-a": "Serie A",
    "premier-league": "Premier League",
    "laliga-santander": "LaLiga EA Sports",
    "bundesliga": "Bundesliga",
    "ligue-1": "Ligue 1 McDonald's",
    "eredivisie": "Eredivisie",
    "liga-portugal": "Liga Portugal Betclic",
    "jupiler-pro-league": "Jupiler Pro League",
    "premiership": "Scottish Premiership (SPFL)",
    "mls": "Major League Soccer (MLS)"
}

TOP_5_LEAGUES = ["premier-league", "laliga-santander", "serie-a", "bundesliga", "ligue-1"]
HOT_STREAK_STEPS = [320, 360, 380, 420, 440, 470, 550]

# Query ufficiale Sorare Football
QUERY_GALLERY = """
query GetUserGallery($slug: String!) {
  user(slug: $slug) {
    id
    slug
    nickname
    footballCards(first: 50) {
      nodes {
        slug
        rarity
        xpBonus
        season {
          startYear
        }
        player {
          slug
          displayName
          position
          activeClub {
            slug
            name
            domesticLeague {
              slug
              name
            }
          }
          lastFiveSo5Scores
          lastFifteenSo5Scores
        }
      }
    }
  }
}
"""

def extract_slug(input_val):
    val = input_val.strip()
    if "my-club/" in val:
        val = val.split("my-club/")[-1].split("?")[0].strip("/")
    elif "sorare.com/" in val:
        val = val.split("/")[-1].split("?")[0]
    return val

def get_demo_cards():
    return [
        {"card_slug": "mike-maignan-2026-limited", "player_slug": "mike-maignan", "name": "Mike Maignan", "position": "Goalkeeper", "rarity": "limited", "season_year": 2026, "is_in_season": True, "multiplier": 1.05, "club_name": "AC Milan", "club_slug": "milan", "league_slug": "serie-a", "league_name": "Serie A", "l5_avg": 54.2, "floor_idx": 45.0, "ceiling_idx": 72.0, "starter_rate": 100.0, "l5_scores": [58, 48, 62, 51, 52], "l15_scores": [58, 48, 62, 51, 52, 60, 42, 68]},
        {"card_slug": "theo-hernandez-2026-limited", "player_slug": "theo-hernandez", "name": "Theo Hernández", "position": "Defender", "rarity": "limited", "season_year": 2026, "is_in_season": True, "multiplier": 1.08, "club_name": "AC Milan", "club_slug": "milan", "league_slug": "serie-a", "league_name": "Serie A", "l5_avg": 62.4, "floor_idx": 48.0, "ceiling_idx": 84.0, "starter_rate": 100.0, "l5_scores": [65, 72, 44, 59, 72], "l15_scores": [65, 72, 44, 59, 72, 80, 52, 63]},
        {"card_slug": "federico-dimarco-2025-limited", "player_slug": "federico-dimarco", "name": "Federico Dimarco", "position": "Defender", "rarity": "limited", "season_year": 2025, "is_in_season": False, "multiplier": 1.03, "club_name": "Inter", "club_slug": "inter", "league_slug": "serie-a", "league_name": "Serie A", "l5_avg": 59.0, "floor_idx": 42.0, "ceiling_idx": 78.0, "starter_rate": 80.0, "l5_scores": [60, 75, 41, 55, 64], "l15_scores": [60, 75, 41, 55, 64, 70, 39, 58]},
        {"card_slug": "teun-koopmeiners-2026-limited", "player_slug": "teun-koopmeiners", "name": "Teun Koopmeiners", "position": "Midfielder", "rarity": "limited", "season_year": 2026, "is_in_season": True, "multiplier": 1.07, "club_name": "Juventus", "club_slug": "juventus", "league_slug": "serie-a", "league_name": "Serie A", "l5_avg": 58.6, "floor_idx": 46.0, "ceiling_idx": 81.0, "starter_rate": 100.0, "l5_scores": [52, 64, 49, 70, 58], "l15_scores": [52, 64, 49, 70, 58, 62, 54, 75]},
        {"card_slug": "nicolo-barella-2026-limited", "player_slug": "nicolo-barella", "name": "Nicolò Barella", "position": "Midfielder", "rarity": "limited", "season_year": 2026, "is_in_season": True, "multiplier": 1.05, "club_name": "Inter", "club_slug": "inter", "league_slug": "serie-a", "league_name": "Serie A", "l5_avg": 56.4, "floor_idx": 44.0, "ceiling_idx": 75.0, "starter_rate": 100.0, "l5_scores": [50, 61, 55, 60, 56], "l15_scores": [50, 61, 55, 60, 56, 68, 48, 59]},
        {"card_slug": "lautaro-martinez-2026-limited", "player_slug": "lautaro-martinez", "name": "Lautaro Martínez", "position": "Forward", "rarity": "limited", "season_year": 2026, "is_in_season": True, "multiplier": 1.10, "club_name": "Inter", "club_slug": "inter", "league_slug": "serie-a", "league_name": "Serie A", "l5_avg": 68.2, "floor_idx": 50.0, "ceiling_idx": 95.0, "starter_rate": 100.0, "l5_scores": [75, 82, 45, 60, 79], "l15_scores": [75, 82, 45, 60, 79, 90, 48, 65]},
        {"card_slug": "marcus-thuram-2026-limited", "player_slug": "marcus-thuram", "name": "Marcus Thuram", "position": "Forward", "rarity": "limited", "season_year": 2026, "is_in_season": True, "multiplier": 1.06, "club_name": "Inter", "club_slug": "inter", "league_slug": "serie-a", "league_name": "Serie A", "l5_avg": 61.5, "floor_idx": 43.0, "ceiling_idx": 88.0, "starter_rate": 100.0, "l5_scores": [55, 78, 48, 62, 64], "l15_scores": [55, 78, 48, 62, 64, 70, 45, 60]}
    ]

@st.cache_data(ttl=300, show_spinner=False)
def fetch_gallery_data(raw_slug):
    user_slug = extract_slug(raw_slug)
    cards_data = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        resp = requests.post(
            API_URL,
            json={"query": QUERY_GALLERY, "variables": {"slug": user_slug}},
            headers=headers,
            timeout=12
        )
        resp_json = resp.json()
        
        if resp.status_code != 200 or "errors" in resp_json:
            err_msg = resp_json.get("errors", [{}])[0].get("message", f"Status {resp.status_code}")
            st.sidebar.error(f"Dettaglio Sorare: {err_msg}")
        else:
            user_node = resp_json.get("data", {}).get("user")
            if user_node:
                cards_conn = user_node.get("footballCards") or {}
                nodes = cards_conn.get("nodes", []) if isinstance(cards_conn, dict) else []
                
                for card in nodes:
                    player = card.get("player")
                    if not player:
                        continue
                    active_club = player.get("activeClub") or {}
                    domestic_league = active_club.get("domesticLeague") or {}
                    card_year = card.get("season", {}).get("startYear", 0)
                    is_in_season = (card_year == IN_SEASON_YEAR)
                    xp_bonus = card.get("xpBonus", 0.0)
                    season_bonus = 0.05 if is_in_season else 0.0
                    card_multiplier = 1.0 + xp_bonus + season_bonus
                    l5 = [x for x in (player.get("lastFiveSo5Scores") or []) if x is not None]
                    l15 = [x for x in (player.get("lastFifteenSo5Scores") or []) if x is not None]
                    if not l5:
                        l5 = [35.0]
                    if not l15:
                        l15 = l5
                    mean_l5 = float(np.mean(l5))
                    floor_idx = float(np.percentile(l15, 20)) if len(l15) >= 3 else mean_l5 * 0.8
                    ceiling_idx = float(np.percentile(l15, 85)) if len(l15) >= 3 else mean_l5 * 1.2
                    starter_rate = float(sum(1 for s in l5 if s >= 35) / len(l5)) * 100.0

                    cards_data.append({
                        "card_slug": card.get("slug"),
                        "player_slug": player.get("slug"),
                        "name": player.get("displayName"),
                        "position": player.get("position"),
                        "rarity": card.get("rarity"),
                        "season_year": card_year,
                        "is_in_season": is_in_season,
                        "multiplier": card_multiplier,
                        "club_name": active_club.get("name", "Svincolato"),
                        "club_slug": active_club.get("slug", ""),
                        "league_slug": domestic_league.get("slug", "serie-a"),
                        "league_name": domestic_league.get("name", "Serie A"),
                        "l5_avg": round(mean_l5, 1),
                        "floor_idx": round(floor_idx, 1),
                        "ceiling_idx": round(ceiling_idx, 1),
                        "starter_rate": round(starter_rate, 1),
                        "l5_scores": l5,
                        "l15_scores": l15
                    })
    except Exception as e:
        st.sidebar.error(f"Errore connessione: {e}")

    if not cards_data:
        cards_data = get_demo_cards()

    return pd.DataFrame(cards_data)

if "locked_cards" not in st.session_state:
    st.session_state["locked_cards"] = set()

if "saved_lineups" not in st.session_state:
    st.session_state["saved_lineups"] = {}

# ==========================================
# SIDEBAR
# ==========================================
st.sidebar.title("⚽ Sorare Pro Hub")
default_slug = "xt_matty-0d7de6d1-d3e9-42c5-b62a-6cd4dbd8d691"
user_input = st.sidebar.text_input("Username o Link Club Sorare", value=default_slug)

if st.sidebar.button("🔄 Sincronizza Dati GW"):
    st.cache_data.clear()
    st.session_state["locked_cards"] = set()
    st.session_state["saved_lineups"] = {}
    st.sidebar.success("Cache aggiornata!")

with st.spinner("Caricamento rosa in corso..."):
    df = fetch_gallery_data(user_input)

st.sidebar.divider()
st.sidebar.subheader("Modalità Target")
game_mode = st.sidebar.radio("Obiettivo Formazione", ["Pro: Hot Streaks (Soglia)", "Arena: Leaderboard (Podio)"])

target_threshold = 380
if game_mode.startswith("Pro"):
    target_threshold = st.sidebar.select_slider(
        "Soglia Obiettivo (Step Hot Streak)",
        options=HOT_STREAK_STEPS,
        value=380
    )

st.sidebar.divider()
st.sidebar.subheader("Competizione Selezionata")

comp_type = st.sidebar.selectbox(
    "Categoria Torneo",
    ["In-Season Domestico (SO5)", "In-Season Coppe Europee (SO5)", "Classic SO7"]
)

selected_competition = ""
if comp_type == "In-Season Domestico (SO5)":
    selected_competition = st.sidebar.selectbox("Campionato", list(DOMESTIC_LEAGUES.values()))
elif comp_type == "In-Season Coppe Europee (SO5)":
    selected_competition = st.sidebar.selectbox("Coppa Europea", ["UEFA Champions League", "UEFA Europa & Conference League"])
else:
    selected_competition = st.sidebar.selectbox("Torneo Classic", ["Champion Europe SO7", "All-Star SO7"])

if st.sidebar.button("🗑️ Sblocca Formazioni"):
    st.session_state["locked_cards"] = set()
    st.session_state["saved_lineups"] = {}
    st.rerun()

def filter_eligible_cards(data, comp_cat, comp_name, exclude_locked=True):
    temp = data.copy()
    if exclude_locked:
        temp = temp[~temp["card_slug"].isin(st.session_state["locked_cards"])]
        
    if comp_cat == "In-Season Domestico (SO5)":
        target_slug = [k for k, v in DOMESTIC_LEAGUES.items() if v == comp_name][0]
        match = temp[temp["league_slug"] == target_slug]
        if not match.empty:
            temp = match
    elif comp_cat == "Classic SO7":
        classic_only = temp[~temp["is_in_season"]]
        if not classic_only.empty:
            temp = classic_only
            
    return temp

eligible_df = filter_eligible_cards(df, comp_type, selected_competition)

tab_builder, tab_h2h, tab_gallery = st.tabs(["🏆 Builder Formazione", "⚔️ Head-to-Head (1v1)", "📊 Rosa & Club Attuali"])

# --- TAB 1: BUILDER ---
with tab_builder:
    st.subheader(f"Composizione: {selected_competition}")
    
    is_so7 = (comp_type == "Classic SO7")
    slots_needed = ["GK", "DEF", "MID", "FWD", "EXTRA"] if not is_so7 else ["GK", "DEF 1", "DEF 2", "MID 1", "MID 2", "FWD", "EXTRA"]
    
    st.caption(f"Formato: {'SO7 (7 Titolari Classic)' if is_so7 else 'SO5 (Min 4 In-Season + Max 1 Classic)'}")
    
    col_layout, col_stats = st.columns([3, 2])
    
    with col_layout:
        st.write("##### Assegnazione Slot Titolari")
        selected_cards = {}
        
        for slot in slots_needed:
            pos_filter = slot.split()[0]
            if pos_filter == "EXTRA":
                candidates = eligible_df[eligible_df["position"] != "Goalkeeper"]
            elif pos_filter in ["GK", "DEF", "MID", "FWD"]:
                role_map = {"GK": "Goalkeeper", "DEF": "Defender", "MID": "Midfielder", "FWD": "Forward"}
                candidates = eligible_df[eligible_df["position"] == role_map[pos_filter]]
            else:
                candidates = eligible_df
                
            already_chosen = [c["card_slug"] for c in selected_cards.values() if c is not None]
            candidates = candidates[~candidates["card_slug"].isin(already_chosen)]
            
            options_dict = {
                f"{row['name']} ({row['club_name']}) - {'🟢 In-S' if row['is_in_season'] else '⚪ Classic'} - L5: {row['l5_avg']}": row['card_slug']
                for _, row in candidates.iterrows()
            }
            options_list = ["-- Vuoto --"] + list(options_dict.keys())
            
            choice = st.selectbox(f"Slot: {slot}", options_list, key=f"sel_{selected_competition}_{slot}")
            
            if choice != "-- Vuoto --":
                c_slug = options_dict[choice]
                selected_cards[slot] = eligible_df[eligible_df["card_slug"] == c_slug].iloc[0]
            else:
                selected_cards[slot] = None
                
    with col_stats:
        st.write("##### Monitoraggio Punteggi Attesi")
        active_lineup = [c for c in selected_cards.values() if c is not None]
        
        if len(active_lineup) == len(slots_needed):
            if not is_so7:
                in_season_count = sum(1 for c in active_lineup if c["is_in_season"])
                if in_season_count < 4:
                    st.error(f"⚠️ Servono almeno 4 carte In-Season! (Attuali: {in_season_count})")
                else:
                    st.success("✅ Requisito In-Season rispettato (Min. 4 carte).")
            
            cap_candidate = max(active_lineup, key=lambda x: x["ceiling_idx"])
            st.info(f"🎖️ **Capitano Consigliato (+50%):** {cap_candidate['name']}")
            
            tot_floor = 0
            tot_ceiling = 0
            for c in active_lineup:
                mult = c["multiplier"] * (1.5 if c["card_slug"] == cap_candidate["card_slug"] else 1.0)
                tot_floor += c["floor_idx"] * mult
                tot_ceiling += c["ceiling_idx"] * mult
                
            st.metric("Floor Previsto Totale", f"{tot_floor:.1f} pt")
            st.metric("Ceiling Potenziale Totale", f"{tot_ceiling:.1f} pt")
            
            if game_mode.startswith("Pro"):
                if tot_floor >= target_threshold:
                    st.success(f"🎯 Target {target_threshold} pt coperto in piena sicurezza dal Floor!")
                elif tot_ceiling >= target_threshold:
                    st.warning(f"⚡ Raggiungibile tramite Ceiling (Floor: {tot_floor:.1f} / Target: {target_threshold})")
                else:
                    st.error(f"❌ Punteggio insufficiente per il target {target_threshold} pt.")
                    
            if st.button("🔒 Salva & Blocca Carte per la GW"):
                for c in active_lineup:
                    st.session_state["locked_cards"].add(c["card_slug"])
                st.session_state["saved_lineups"][selected_competition] = active_lineup
                st.success("Formazione registrata: carte bloccate per i restanti tornei!")
                st.rerun()
        else:
            st.info(f"Seleziona tutti i {len(slots_needed)} slot per visualizzare le metriche.")

# --- TAB 2: HEAD TO HEAD ---
with tab_h2h:
    st.subheader("⚔️ Confronto Diretto Ballottaggi")
    col1, col2 = st.columns(2)
    
    card_list = {f"{row['name']} ({row['club_name']}) - #{row['card_slug'].split('-')[-1]}": row['card_slug'] for _, row in df.iterrows()}
    
    with col1:
        c1_key = st.selectbox("Seleziona Carta A", list(card_list.keys()), index=0)
        p1 = df[df["card_slug"] == card_list[c1_key]].iloc[0]
        st.markdown(f"### {p1['name']}")
        st.caption(f"Squadra: **{p1['club_name']}** ({p1['league_name']})")
        st.write(f"• **Stagione:** {'🟢 In-Season' if p1['is_in_season'] else '⚪ Classic'}")
        st.write(f"• **Moltiplicatore Totale:** x{p1['multiplier']:.2f}")
        st.write(f"• **Titolarità L5:** {p1['starter_rate']}%")
        st.metric("Floor Index", f"{p1['floor_idx']} pt")
        st.metric("Ceiling Index", f"{p1['ceiling_idx']} pt")
        st.write(f"Ultime 5 partite: `{p1['l5_scores']}`")

    with col2:
        c2_key = st.selectbox("Seleziona Carta B", list(card_list.keys()), index=min(1, len(card_list)-1))
        p2 = df[df["card_slug"] == card_list[c2_key]].iloc[0]
        st.markdown(f"### {p2['name']}")
        st.caption(f"Squadra: **{p2['club_name']}** ({p2['league_name']})")
        st.write(f"• **Stagione:** {'🟢 In-Season' if p2['is_in_season'] else '⚪ Classic'}")
        st.write(f"• **Moltiplicatore Totale:** x{p2['multiplier']:.2f}")
        st.write(f"• **Titolarità L5:** {p2['starter_rate']}%")
        st.metric("Floor Index", f"{p2['floor_idx']} pt")
        st.metric("Ceiling Index", f"{p2['ceiling_idx']} pt")
        st.write(f"Ultime 5 partite: `{p2['l5_scores']}`")
        
    st.divider()
    st.write("##### Suggerimento Algoritmo")
    if p1["floor_idx"] > p2["floor_idx"]:
        st.info(f"🛡️ **Sicurezza Soglia (Floor):** Consigliato **{p1['name']}** (+{p1['floor_idx'] - p2['floor_idx']:.1f} pt)")
    else:
        st.info(f"🛡️ **Sicurezza Soglia (Floor):** Consigliato **{p2['name']}** (+{p2['floor_idx'] - p1['floor_idx']:.1f} pt)")
        
    if p1["ceiling_idx"] > p2["ceiling_idx"]:
        st.success(f"🚀 **Potenziale Podio (Ceiling):** Consigliato **{p1['name']}** (+{p1['ceiling_idx'] - p2['ceiling_idx']:.1f} pt)")
    else:
        st.success(f"🚀 **Potenziale Podio (Ceiling):** Consigliato **{p2['name']}** (+{p2['ceiling_idx'] - p1['ceiling_idx']:.1f} pt)")

# --- TAB 3: ROSA E CLUB ---
with tab_gallery:
    st.subheader("📊 Rosa Completa & Club Contemporaneo")
    display_df = df[["name", "club_name", "league_name", "position", "is_in_season", "multiplier", "l5_avg", "floor_idx", "ceiling_idx", "card_slug"]].copy()
    display_df["is_in_season"] = display_df["is_in_season"].apply(lambda x: "In-Season (2026)" if x else "Classic")
    display_df["is_locked"] = display_df["card_slug"].apply(lambda x: "🔒 Schierato" if x in st.session_state["locked_cards"] else "🟢 Libero")
    
    st.dataframe(
        display_df,
        column_config={
            "name": "Calciatore",
            "club_name": "Club Attuale (Opta)",
            "league_name": "Lega Attuale",
            "position": "Ruolo",
            "is_in_season": "Stagionalità",
            "multiplier": "Moltiplicatore",
            "l5_avg": "Media L5",
            "floor_idx": "Floor",
            "ceiling_idx": "Ceiling",
            "is_locked": "Stato GW"
        },
        use_container_width=True,
        hide_index=True
    )
