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

# Campionati domestici disponibili (Serie A rimossa dai tornei singoli)
DOMESTIC_LEAGUES = {
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

# Query GraphQL corretta e compatibile con lo schema Card di Sorare
QUERY_USER_GALLERY = """
query GetUserGalleryCards($slug: String!) {
  user(slug: $slug) {
    nickname
    cards {
      nodes {
        slug
        rarityTyped
        ... on Card {
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
}
"""

def extract_slug(input_val):
    val = input_val.strip()
    if "my-club/" in val:
        val = val.split("my-club/")[-1].split("?")[0].strip("/")
    elif "sorare.com/" in val:
        val = val.split("/")[-1].split("?")[0]
    return val

@st.cache_data(ttl=300, show_spinner=False)
def fetch_gallery_data(raw_slug):
    user_slug = extract_slug(raw_slug)
    cards_data = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        resp = requests.post(
            API_URL,
            json={"query": QUERY_USER_GALLERY, "variables": {"slug": user_slug}},
            headers=headers,
            timeout=15
        )
        resp_json = resp.json()
        
        if resp.status_code != 200 or "errors" in resp_json:
            err_msg = resp_json.get("errors", [{}])[0].get("message", f"Status {resp.status_code}")
            st.sidebar.error(f"Dettaglio Sorare: {err_msg}")
            return pd.DataFrame()
            
        user_node = resp_json.get("data", {}).get("user")
        if not user_node:
            st.sidebar.warning("Utente non trovato su Sorare.")
            return pd.DataFrame()
            
        cards_connection = user_node.get("cards", {}) or {}
        nodes = cards_connection.get("nodes", []) if isinstance(cards_connection, dict) else []
        
        for card in nodes:
            player = card.get("player")
            if not player:
                continue
            active_club = player.get("activeClub") or {}
            domestic_league = active_club.get("domesticLeague") or {}
            card_year = card.get("season", {}).get("startYear", 0)
            is_in_season = (card_year == IN_SEASON_YEAR)
            season_bonus = 0.05 if is_in_season else 0.0
            card_multiplier = 1.0 + season_bonus
            
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
                "rarity": card.get("rarityTyped", "limited"),
                "season_year": card_year,
                "is_in_season": is_in_season,
                "multiplier": card_multiplier,
                "club_name": active_club.get("name", "Svincolato"),
                "club_slug": active_club.get("slug", ""),
                "league_slug": domestic_league.get("slug", "other"),
                "league_name": domestic_league.get("name", "Altro"),
                "l5_avg": round(mean_l5, 1),
                "floor_idx": round(floor_idx, 1),
                "ceiling_idx": round(ceiling_idx, 1),
                "starter_rate": round(starter_rate, 1),
                "l5_scores": l5,
                "l15_scores": l15
            })
    except Exception as e:
        st.sidebar.error(f"Errore connessione: {e}")

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

with st.spinner("Scaricamento della tua galleria Sorare..."):
    df = fetch_gallery_data(user_input)

if df.empty:
    st.warning("Nessuna carta trovata per questo account o recupero in corso. Se il caricamento fallisce, controlla il messaggio di errore nella barra laterale.")
    st.stop()

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
    ["In-Season Domestico (SO5)", "In-Season Coppe Europee (SO5)", "Classic SO7", "Tutte le Carte (Libero)"]
)

selected_competition = ""
if comp_type == "In-Season Domestico (SO5)":
    selected_competition = st.sidebar.selectbox("Campionato Singolo", list(DOMESTIC_LEAGUES.values()))
elif comp_type == "In-Season Coppe Europee (SO5)":
    selected_competition = st.sidebar.selectbox("Coppa Europea", ["UEFA Champions League", "UEFA Europa & Conference League"])
elif comp_type == "Classic SO7":
    selected_competition = st.sidebar.selectbox("Torneo Classic", ["Champion Europe SO7", "All-Star SO7"])
else:
    selected_competition = "Tutta la Galleria"

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
        temp = temp[temp["league_slug"] == target_slug]
    elif comp_cat == "Classic SO7":
        temp = temp[~temp["is_in_season"]]
        if comp_name == "Champion Europe SO7":
            temp = temp[temp["league_slug"].isin(TOP_5_LEAGUES)]
    return temp

eligible_df = filter_eligible_cards(df, comp_type, selected_competition)

tab_builder, tab_h2h, tab_gallery = st.tabs(["🏆 Builder Formazione", "⚔️ Head-to-Head (1v1)", "📊 Rosa Completa"])

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
                f"{row['name']} ({row['club_name']} - {row['league_name']}) - {'🟢 In-S' if row['is_in_season'] else '⚪ Classic'} - L5: {row['l5_avg']}": row['card_slug']
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
            if not is_so7 and comp_type != "Tutte le Carte (Libero)":
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
    
    card_list = {f"{row['name']} ({row['club_name']} - {row['league_name']})": row['card_slug'] for _, row in df.iterrows()}
    
    if card_list:
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

# --- TAB 3: ROSA GENERALE ---
with tab_gallery:
    st.subheader("📊 Tutte le Tue Carte Sorare")
    display_df = df[["name", "club_name", "league_name", "position", "is_in_season", "multiplier", "l5_avg", "floor_idx", "ceiling_idx", "card_slug"]].copy()
    display_df["is_in_season"] = display_df["is_in_season"].apply(lambda x: "In-Season (2026)" if x else "Classic")
    display_df["is_locked"] = display_df["card_slug"].apply(lambda x: "🔒 Schierato" if x in st.session_state["locked_cards"] else "🟢 Libero")
    
    st.dataframe(
        display_df,
        column_config={
            "name": "Calciatore",
            "club_name": "Club Attuale",
            "league_name": "Campionato",
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
