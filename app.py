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

# Riconoscimento rigoroso TOP 5 LEGHE di PRIMA DIVISIONE
# La Serie A è inclusa qui per Champion ma non ha la sua sezione a campionato singolo
TOP_5_FIRST_DIVISION_SLUGS = [
    "premier-league",
    "england-premier-league",
    "laliga-santander",
    "spain-laliga",
    "serie-a",
    "italy-serie-a",
    "bundesliga",
    "germany-bundesliga",
    "ligue-1",
    "france-ligue-1"
]

# Esclusioni categoriche da Champion (seconde divisioni o leghe minori)
EXCLUDED_FROM_TOP_5 = [
    "bundesliga-2", "2-bundesliga", "germany-2", "segunda", "laliga-2",
    "championship", "serie-b", "ligue-2", "premiership", "scotland"
]

# Campionati Challenger Europe (leghe europee primarie non top 5)
CHALLENGER_LEAGUE_SLUGS = [
    "eredivisie", "netherlands-eredivisie",
    "liga-portugal", "portugal-primeira-liga",
    "jupiler-pro-league", "belgium-pro-league",
    "premiership", "scotland-premiership",
    "super-lig", "turkey-super-lig",
    "austrian-bundesliga", "swiss-super-league"
]

# Campionati domestici singoli disponibili (Serie A rimossa dai tornei singoli)
DOMESTIC_LEAGUES_MAP = {
    "Premier League": ["premier-league", "england-premier-league"],
    "LaLiga EA Sports": ["laliga-santander", "spain-laliga"],
    "Bundesliga (1. Divisione)": ["bundesliga", "germany-bundesliga"],
    "Ligue 1": ["ligue-1", "france-ligue-1"],
    "Eredivisie": ["eredivisie", "netherlands-eredivisie"],
    "Liga Portugal": ["liga-portugal", "portugal-primeira-liga"],
    "Jupiler Pro League": ["jupiler-pro-league", "belgium-pro-league"],
    "Scottish Premiership": ["premiership", "scotland-premiership"],
    "MLS": ["mls", "major-league-soccer"]
}

# Club partecipanti a UEFA Champions League
UCL_CLUBS_KEYWORDS = [
    "manchester city", "arsenal", "liverpool", "aston villa",
    "real madrid", "barcelona", "atlético", "atletico", "girona",
    "inter", "milan", "juventus", "atalanta", "bologna",
    "bayern", "leverkusen", "dortmund", "leipzig", "stuttgart",
    "paris saint-germain", "psg", "monaco", "brest", "lille",
    "sporting cp", "benfica", "porto", "feyenoord", "psv",
    "celtic", "club brugge", "shakhtar", "dinamo zagreb", "salzburg", "young boys", "crvena zvezda", "sparta praha", "sturm graz"
]

# Club partecipanti a UEFA Europa League & Conference League
UEL_UECL_CLUBS_KEYWORDS = [
    "manchester united", "tottenham", "chelsea",
    "roma", "lazio", "fiorentina",
    "real sociedad", "athletic club", "real betis",
    "frankfurt", "hoffenheim", "heidenheim",
    "nice", "lyon", "lens",
    "porto", "braga", "vitória", "guimaraes",
    "ajax", "twente", "alkmaar", "az",
    "anderlecht", "union saint-gilloise", "gent", "cercle brugge",
    "rangers", "heart", "hearts", "aberdeen",
    "galatasaray", "fenerbahce", "besiktas", "basaksehir",
    "olympiacos", "paok", "panathinaikos", "slavia praha", "viktoria plzen", "bodo/glimt", "malmo"
]

HOT_STREAK_STEPS = [320, 360, 380, 420, 440, 470, 550]

QUERY_USER_GALLERY = """
query GetUserGalleryCards($slug: String!, $cursor: String) {
  user(slug: $slug) {
    cards(first: 20, after: $cursor) {
      pageInfo {
        hasNextPage
        endCursor
      }
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
              name
              domesticLeague {
                slug
                name
              }
            }
            lastFiveSo5Appearances
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
    cursor = None
    has_next = True
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    while has_next:
        variables = {"slug": user_slug, "cursor": cursor}
        try:
            resp = requests.post(
                API_URL,
                json={"query": QUERY_USER_GALLERY, "variables": variables},
                headers=headers,
                timeout=15
            )
            resp_json = resp.json()
            
            if resp.status_code != 200 or "errors" in resp_json:
                err_msg = resp_json.get("errors", [{}])[0].get("message", f"Status {resp.status_code}")
                st.sidebar.error(f"Dettaglio Sorare: {err_msg}")
                break
                
            user_node = resp_json.get("data", {}).get("user")
            if not user_node:
                break
                
            cards_connection = user_node.get("cards", {}) or {}
            nodes = cards_connection.get("nodes", []) if isinstance(cards_connection, dict) else []
            
            for card in nodes:
                # FILTRO RIGIDO: SOLO LIMITED
                rarity = str(card.get("rarityTyped", "")).lower()
                if rarity != "limited":
                    continue

                player = card.get("player")
                if not player:
                    continue
                active_club = player.get("activeClub") or {}
                domestic_league = active_club.get("domesticLeague") or {}
                card_year = card.get("season", {}).get("startYear", 0)
                is_in_season = (card_year == IN_SEASON_YEAR)
                season_bonus = 0.05 if is_in_season else 0.0
                card_multiplier = 1.0 + season_bonus
                
                l5_apps = player.get("lastFiveSo5Appearances", 0) or 0
                starter_rate = round(min(100.0, (l5_apps / 5.0) * 100.0), 1)
                
                mean_l5 = 54.0 if starter_rate >= 80 else (45.0 if starter_rate >= 40 else 35.0)
                floor_idx = round(mean_l5 * 0.8, 1)
                ceiling_idx = round(mean_l5 * 1.35, 1)

                raw_pos = str(player.get("position", "")).strip().upper()
                l_slug = str(domestic_league.get("slug", "")).lower().strip()
                l_name = str(domestic_league.get("name", "Altro"))
                club_n = str(active_club.get("name", "Svincolato"))

                cards_data.append({
                    "card_slug": card.get("slug"),
                    "player_slug": player.get("slug"),
                    "name": player.get("displayName"),
                    "position": raw_pos,
                    "rarity": "Limited",
                    "season_year": card_year,
                    "is_in_season": is_in_season,
                    "multiplier": card_multiplier,
                    "club_name": club_n,
                    "club_lower": club_n.lower(),
                    "league_slug": l_slug,
                    "league_name": l_name,
                    "l5_avg": round(mean_l5, 1),
                    "floor_idx": floor_idx,
                    "ceiling_idx": ceiling_idx,
                    "starter_rate": starter_rate,
                    "l5_apps": l5_apps
                })
                
            page_info = cards_connection.get("pageInfo", {})
            has_next = page_info.get("hasNextPage", False)
            cursor = page_info.get("endCursor")
        except Exception as e:
            st.sidebar.error(f"Errore connessione: {e}")
            break

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

with st.spinner("Scaricamento delle tue carte Limited..."):
    df = fetch_gallery_data(user_input)

if df.empty:
    st.warning("Nessuna carta Limited trovata per questo account.")
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
    [
        "Champion Europe (Top 5 Leghe)",
        "Challenger Europe",
        "UEFA Champions League",
        "UEFA Europa & Conference League",
        "Campionato Singolo Domestico",
        "All-Star (Tutti i campionati)"
    ]
)

selected_competition = ""
single_league_choice = ""

if comp_type == "Champion Europe (Top 5 Leghe)":
    sub_format = st.sidebar.radio("Formato Champion", ["Classic SO7", "In-Season SO5", "Classic SO5"])
    selected_competition = f"Champion Europe ({sub_format})"
elif comp_type == "Challenger Europe":
    sub_format = st.sidebar.radio("Formato Challenger", ["Classic SO7", "In-Season SO5", "Classic SO5"])
    selected_competition = f"Challenger Europe ({sub_format})"
elif comp_type == "UEFA Champions League":
    sub_format = st.sidebar.radio("Formato UCL", ["In-Season SO5", "Classic SO5"])
    selected_competition = f"UEFA Champions League ({sub_format})"
elif comp_type == "UEFA Europa & Conference League":
    sub_format = st.sidebar.radio("Formato UEL/UECL", ["In-Season SO5", "Classic SO5"])
    selected_competition = f"UEFA Europa & Conference League ({sub_format})"
elif comp_type == "Campionato Singolo Domestico":
    single_league_choice = st.sidebar.selectbox("Scegli Campionato", list(DOMESTIC_LEAGUES_MAP.keys()), index=0)
    selected_competition = f"{single_league_choice}"
else:
    selected_competition = "All-Star (Tutti i campionati)"

if st.sidebar.button("🗑️ Sblocca Formazioni"):
    st.session_state["locked_cards"] = set()
    st.session_state["saved_lineups"] = {}
    st.rerun()

# Filtraggio rigoroso
def is_top_5_league(slug):
    # Deve contenere una top 5 ma NON contenere divisioni inferiori
    is_match = any(top in slug for top in TOP_5_FIRST_DIVISION_SLUGS)
    is_excluded = any(exc in slug for exc in EXCLUDED_FROM_TOP_5)
    return is_match and not is_excluded

def filter_eligible_cards(data, main_cat, comp_name, single_choice, exclude_locked=True):
    temp = data.copy()
    if exclude_locked:
        temp = temp[~temp["card_slug"].isin(st.session_state["locked_cards"])]
        
    if main_cat == "Champion Europe (Top 5 Leghe)":
        temp = temp[temp["league_slug"].apply(is_top_5_league)]
        if "In-Season" in comp_name:
            temp = temp[temp["is_in_season"]]

    elif main_cat == "Challenger Europe":
        temp = temp[temp["league_slug"].apply(lambda s: any(ch_slug in s for ch_slug in CHALLENGER_LEAGUE_SLUGS))]
        if "In-Season" in comp_name:
            temp = temp[temp["is_in_season"]]

    elif main_cat == "UEFA Champions League":
        pattern = "|".join(UCL_CLUBS_KEYWORDS)
        temp = temp[temp["club_lower"].str.contains(pattern, na=False)]
        if "In-Season" in comp_name:
            temp = temp[temp["is_in_season"]]

    elif main_cat == "UEFA Europa & Conference League":
        pattern = "|".join(UEL_UECL_CLUBS_KEYWORDS)
        temp = temp[temp["club_lower"].str.contains(pattern, na=False)]
        if "In-Season" in comp_name:
            temp = temp[temp["is_in_season"]]

    elif main_cat == "Campionato Singolo Domestico":
        allowed_slugs = DOMESTIC_LEAGUES_MAP.get(single_choice, [])
        if "Bundesliga" in single_choice:
            temp = temp[temp["league_slug"].apply(lambda s: any(t in s for t in allowed_slugs) and not any(e in s for e in EXCLUDED_FROM_TOP_5))]
        else:
            temp = temp[temp["league_slug"].apply(lambda s: any(target in s for target in allowed_slugs))]

    elif main_cat == "All-Star (Tutti i campionati)":
        pass
        
    return temp

eligible_df = filter_eligible_cards(df, comp_type, selected_competition, single_league_choice)

tab_builder, tab_h2h, tab_gallery = st.tabs(["🏆 Builder Formazione", "⚔️ Head-to-Head (1v1)", "📊 Rosa Limited"])

# --- TAB 1: BUILDER ---
with tab_builder:
    st.subheader(f"Composizione: {selected_competition}")
    
    is_so7 = ("SO7" in selected_competition)
    slots_needed = ["GK", "DEF", "MID", "FWD", "EXTRA"] if not is_so7 else ["GK", "DEF 1", "DEF 2", "MID 1", "MID 2", "FWD", "EXTRA"]
    
    st.caption(f"Carte Limited disponibili per questa competizione: **{len(eligible_df)}**")
    
    if eligible_df.empty:
        st.warning("Nessuna carta Limited corrisponde ai criteri di questa specifica competizione.")
    else:
        col_layout, col_stats = st.columns([3, 2])
        
        with col_layout:
            st.write("##### Assegnazione Slot Titolari")
            selected_cards = {}
            
            for slot in slots_needed:
                pos_filter = slot.split()[0]
                if pos_filter == "EXTRA":
                    candidates = eligible_df[~eligible_df["position"].str.contains("GOALKEEPER|GK", na=False)]
                elif pos_filter == "GK":
                    candidates = eligible_df[eligible_df["position"].str.contains("GOALKEEPER|GK", na=False)]
                elif pos_filter == "DEF":
                    candidates = eligible_df[eligible_df["position"].str.contains("DEFENDER|DEF", na=False)]
                elif pos_filter == "MID":
                    candidates = eligible_df[eligible_df["position"].str.contains("MIDFIELDER|MID", na=False)]
                elif pos_filter == "FWD":
                    candidates = eligible_df[eligible_df["position"].str.contains("FORWARD|FWD", na=False)]
                else:
                    candidates = eligible_df
                    
                already_chosen = [c["card_slug"] for c in selected_cards.values() if c is not None]
                candidates = candidates[~candidates["card_slug"].isin(already_chosen)]
                
                options_dict = {
                    f"{row['name']} ({row['club_name']} - {row['league_name']}) - {'🟢 In-S' if row['is_in_season'] else '⚪ Classic'} - L5: {row['l5_apps']}/5": row['card_slug']
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
                if "In-Season" in selected_competition:
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
    st.subheader("⚔️ Confronto Diretto Ballottaggi (Solo Limited)")
    col1, col2 = st.columns(2)
    
    card_list = {f"{row['name']} ({row['club_name']} - {row['league_name']})": row['card_slug'] for _, row in df.iterrows()}
    
    if card_list:
        with col1:
            c1_key = st.selectbox("Seleziona Carta A", list(card_list.keys()), index=0)
            p1 = df[df["card_slug"] == card_list[c1_key]].iloc[0]
            st.markdown(f"### {p1['name']}")
            st.caption(f"Squadra: **{p1['club_name']}** ({p1['league_name']})")
            st.write(f"• **Rarità:** 🟡 Limited")
            st.write(f"• **Stagione:** {'🟢 In-Season' if p1['is_in_season'] else '⚪ Classic'}")
            st.write(f"• **Moltiplicatore Totale:** x{p1['multiplier']:.2f}")
            st.write(f"• **Titolarità L5:** {p1['starter_rate']}% ({p1['l5_apps']}/5)")
            st.metric("Floor Index", f"{p1['floor_idx']} pt")
            st.metric("Ceiling Index", f"{p1['ceiling_idx']} pt")

        with col2:
            c2_key = st.selectbox("Seleziona Carta B", list(card_list.keys()), index=min(1, len(card_list)-1))
            p2 = df[df["card_slug"] == card_list[c2_key]].iloc[0]
            st.markdown(f"### {p2['name']}")
            st.caption(f"Squadra: **{p2['club_name']}** ({p2['league_name']})")
            st.write(f"• **Rarità:** 🟡 Limited")
            st.write(f"• **Stagione:** {'🟢 In-Season' if p2['is_in_season'] else '⚪ Classic'}")
            st.write(f"• **Moltiplicatore Totale:** x{p2['multiplier']:.2f}")
            st.write(f"• **Titolarità L5:** {p2['starter_rate']}% ({p2['l5_apps']}/5)")
            st.metric("Floor Index", f"{p2['floor_idx']} pt")
            st.metric("Ceiling Index", f"{p2['ceiling_idx']} pt")

# --- TAB 3: ROSA GENERALE ---
with tab_gallery:
    st.subheader("📊 Rosa Ufficiale Limited")
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
