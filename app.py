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

TOP_5_PATTERNS = ["premier", "laliga", "serie-a", "serie a", "bundesliga", "ligue 1", "ligue-1"]

EXCLUDED_PATTERNS = [
    "scotland", "premiership", "spfl", "scottish",
    "bundesliga-2", "2-bundesliga", "2. bundesliga",
    "segunda", "serie-b", "serie b", "ligue-2", "ligue 2",
    "championship", "austria", "austrian", "swiss", "switzerland",
    "brazil", "brasileirao", "brasileiro", "argentina", "superliga-argentina", "libertadores", "sudamericana"
]

CHALLENGER_PATTERNS = [
    "scotland", "premiership", "spfl", "portugal", "primeira", "betclic",
    "eredivisie", "netherlands", "jupiler", "belgium", "super-lig", "turkey",
    "austria", "austrian", "swiss", "switzerland", "denmark", "superliga"
]

DOMESTIC_LEAGUES_MAP = {
    "Premier League": "premier-league",
    "LaLiga EA Sports": "laliga",
    "Bundesliga (1. Divisione)": "bundesliga",
    "Ligue 1": "ligue-1",
    "Liga Portugal": "portugal",
    "Eredivisie": "eredivisie",
    "Jupiler Pro League": "jupiler",
    "Scottish Premiership": "scotland",
    "MLS": "mls"
}

UCL_CLUBS_2026_27 = [
    "porto", "fc porto", "futebol clube do porto",
    "manchester city", "arsenal", "liverpool", "aston villa", "manchester united",
    "real madrid", "barcelona", "atlético", "atletico", "villarreal", "real betis",
    "inter", "inter milan", "napoli", "roma", "as roma", "como",
    "bayern", "bayern munchen", "borussia dortmund", "dortmund", "leipzig", "stuttgart",
    "paris saint-germain", "psg", "lille", "lens",
    "sporting cp", "sporting", "psv", "feyenoord",
    "club brugge", "shakhtar", "bodo", "bodo/glimt",
    "galatasaray", "fenerbahce", "fenerbahçe",
    "slavia", "slavia praha", "lask", "viking",
    "slovan bratislava", "aek athens"
]

UEL_UECL_CLUBS_2026_27 = [
    "braga", "sc braga", "sporting braga",
    "benfica", "sl benfica", "vitoria", "guimaraes",
    "milan", "ac milan", "juventus", "lazio", "atalanta", "bologna",
    "tottenham", "chelsea", "newcastle",
    "real sociedad", "athletic club", "celta vigo",
    "bayer leverkusen", "leverkusen", "frankfurt", "hoffenheim", "heidenheim",
    "marseille", "lyon", "olympique lyonnais", "nice", "monaco", "brest",
    "ajax", "az alkmaar", "alkmaar", "twente", "utrecht",
    "anderlecht", "union saint-gilloise", "gent", "genk", "cercle brugge",
    "celtic", "rangers", "heart", "hearts", "aberdeen",
    "besiktas", "basaksehir", "trabzonspor",
    "olympiacos", "paok", "panathinaikos", "viktoria plzen", "sparta praha",
    "young boys", "basel", "salzburg", "sturm graz", "rapid wien"
]

HOT_STREAK_STEPS = [320, 360, 380, 420, 440, 470, 550]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def extract_slug(input_val):
    val = input_val.strip()
    if "my-club/" in val:
        val = val.split("my-club/")[-1].split("?")[0].strip("/")
    elif "sorare.com/" in val:
        val = val.split("/")[-1].split("?")[0]
    return val

def normalize_club_name(name):
    clean = str(name).strip()
    low = clean.lower()
    if "porto" in low:
        return "FC Porto"
    if "benfica" in low:
        return "SL Benfica"
    if "sporting" in low and "braga" not in low:
        return "Sporting CP"
    if "braga" in low:
        return "Sporting Braga"
    if "fenerbah" in low:
        return "Fenerbahçe"
    return clean

# Query per estrarre il club emittente della CARTA (non solo activeClub del giocatore)
QUERY_CARDS = """
query GetUserCards($slug: String!,$cursor: String) {
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
          positionTyped
          grade
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
            lastFiveSo5Appearances
          }
        }
      }
    }
  }
}
"""

@st.cache_data(ttl=300, show_spinner=False)
def fetch_raw_cards(raw_slug):
    user_slug = extract_slug(raw_slug)
    raw_cards = []
    cursor = None
    has_next = True
    
    while has_next:
        variables = {"slug": user_slug, "cursor": cursor}
        try:
            resp = requests.post(
                API_URL,
                json={"query": QUERY_CARDS, "variables": variables},
                headers=HEADERS,
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
                # FILTRO RIGIDO: Solo Limited
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
                grade_val = int(card.get("grade") or 0)

                # DETERMINAZIONE DEL CLUB DELLA CARTA (PER L'ALBUM COLLEZIONE):
                # Se la carta ha uno slug tipo "mateus-fernandes-2023-limited-12",
                # o se il club di emissione coincide con il club noto:
                active_club_name = str(active_club.get("name", "Svincolato"))
                card_club_name = normalize_club_name(active_club_name)

                l5_apps = player.get("lastFiveSo5Appearances", 0) or 0
                starter_rate = round(min(100.0, (l5_apps / 5.0) * 100.0), 1)
                
                mean_l5 = 54.0 if starter_rate >= 80 else (45.0 if starter_rate >= 40 else 35.0)
                floor_idx = round(mean_l5 * 0.8, 1)
                ceiling_idx = round(mean_l5 * 1.35, 1)

                card_pos = card.get("positionTyped")
                if not card_pos:
                    card_pos = player.get("position", "")
                norm_pos = str(card_pos).strip().upper()

                l_slug = str(domestic_league.get("slug", "")).lower().strip()
                l_name = str(domestic_league.get("name", "Altro"))
                league_full_text = f"{l_name} {l_slug}".lower()

                raw_cards.append({
                    "card_slug": card.get("slug"),
                    "player_slug": player.get("slug"),
                    "name": player.get("displayName"),
                    "position": norm_pos,
                    "rarity": "Limited",
                    "season_year": card_year,
                    "grade": grade_val,
                    "is_in_season": is_in_season,
                    "club_name": card_club_name,
                    "club_lower": card_club_name.lower(),
                    "active_club_current": active_club_name,
                    "league_slug": l_slug,
                    "league_name": l_name,
                    "league_text": league_full_text,
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

    return pd.DataFrame(raw_cards)

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

with st.spinner("Scaricamento della rosa Limited da Sorare..."):
    df_raw = fetch_raw_cards(user_input)

if df_raw.empty:
    st.warning("Nessuna carta Limited trovata per questo account.")
    st.stop()

# ==========================================
# GESTIONE PRECISA BONUS COLLEZIONI CLUB
# ==========================================
st.sidebar.divider()
st.sidebar.subheader("🏆 Bonus Collezioni Club")

is_clubs = sorted(list(df_raw[df_raw["is_in_season"]]["club_name"].unique()))
classic_clubs = sorted(list(df_raw[~df_raw["is_in_season"]]["club_name"].unique()))

club_bonus_map = {}

# Sezione 1: Album In-Season (Stagione 2026/27)
with st.sidebar.expander("🟢 Album In-Season 2026/27", expanded=True):
    for c in is_clubs:
        # Benfica In-Season al 5.0% di default
        default_is = 5.0 if "benfica" in c.lower() else (2.0 if "porto" in c.lower() else 0.0)
        val_is = st.number_input(
            f"{c} In-Season (%)",
            min_value=0.0,
            max_value=5.0,
            step=1.0,
            value=default_is,
            key=f"b_is_{c}"
        )
        club_bonus_map[(c, True)] = val_is

# Sezione 2: Album Classic (2025 e precedenti - completamente separati)
with st.sidebar.expander("⚪ Album Classic", expanded=True):
    for c in classic_clubs:
        default_cl = 1.0 if ("porto" in c.lower() or "benfica" in c.lower()) else 0.0
        val_cl = st.number_input(
            f"{c} Classic (%)",
            min_value=0.0,
            max_value=5.0,
            step=1.0,
            value=default_cl,
            key=f"b_cl_{c}"
        )
        club_bonus_map[(c, False)] = val_cl

processed_rows = []
for _, row in df_raw.iterrows():
    c_name = row["club_name"]
    is_in_s = row["is_in_season"]
    
    # 1. LIVELLO XP: 1% per livello esatto
    level_bonus = float(row["grade"]) * 1.0
    
    # 2. STAGIONALE: +5% se In-Season, 0% Classic
    season_bonus = 5.0 if is_in_s else 0.0
    
    # 3. BONUS COLLEZIONE: recuperato in base all'album esatto della carta
    coll_bonus = float(club_bonus_map.get((c_name, is_in_s), 0.0))
    
    total_bonus = round(level_bonus + season_bonus + coll_bonus, 1)
    card_mult = 1.0 + (total_bonus / 100.0)
    
    r_dict = dict(row)
    r_dict["level_bonus"] = level_bonus
    r_dict["collection_bonus"] = coll_bonus
    r_dict["season_bonus"] = season_bonus
    r_dict["bonus_pct"] = total_bonus
    r_dict["multiplier"] = card_mult
    processed_rows.append(r_dict)

df = pd.DataFrame(processed_rows)

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
    sub_format = st.sidebar.radio("Formato Champion", ["Classic SO7", "In-Season SO5"])
    selected_competition = f"Champion Europe ({sub_format})"
elif comp_type == "Challenger Europe":
    sub_format = st.sidebar.radio("Formato Challenger", ["Classic SO7", "In-Season SO5"])
    selected_competition = f"Challenger Europe ({sub_format})"
elif comp_type == "UEFA Champions League":
    sub_format = st.sidebar.radio("Formato UCL", ["Classic SO7", "In-Season SO5"])
    selected_competition = f"UEFA Champions League ({sub_format})"
elif comp_type == "UEFA Europa & Conference League":
    sub_format = st.sidebar.radio("Formato UEL/UECL", ["Classic SO7", "In-Season SO5"])
    selected_competition = f"UEFA Europa & Conference League ({sub_format})"
elif comp_type == "Campionato Singolo Domestico":
    single_league_choice = st.sidebar.selectbox("Scegli Campionato", list(DOMESTIC_LEAGUES_MAP.keys()), index=0)
    selected_competition = f"{single_league_choice} (In-Season SO5)"
else:
    selected_competition = "All-Star (Classic SO7)"

if st.sidebar.button("🗑️ Sblocca Formazioni"):
    st.session_state["locked_cards"] = set()
    st.session_state["saved_lineups"] = {}
    st.rerun()

def check_is_top_5(row):
    text = row["league_text"]
    if any(exc in text for exc in EXCLUDED_PATTERNS):
        return False
    return any(p in text for p in TOP_5_PATTERNS)

def filter_eligible_cards(data, main_cat, comp_name, single_choice, exclude_locked=True):
    temp = data.copy()
    if exclude_locked:
        temp = temp[~temp["card_slug"].isin(st.session_state["locked_cards"])]
        
    if main_cat == "Champion Europe (Top 5 Leghe)":
        temp = temp[temp.apply(check_is_top_5, axis=1)]

    elif main_cat == "Challenger Europe":
        temp = temp[~temp.apply(check_is_top_5, axis=1)]
        temp = temp[temp["league_text"].apply(lambda s: any(k in s for k in CHALLENGER_PATTERNS))]

    elif main_cat == "UEFA Champions League":
        temp = temp[~temp["club_lower"].str.contains("braga|benfica|fiorentina", na=False)]
        pattern = "|".join(UCL_CLUBS_2026_27)
        temp = temp[temp["club_lower"].str.contains(pattern, na=False)]

    elif main_cat == "UEFA Europa & Conference League":
        temp = temp[~temp["club_lower"].str.contains("fiorentina", na=False)]
        pattern = "|".join(UEL_UECL_CLUBS_2026_27)
        temp = temp[temp["club_lower"].str.contains(pattern, na=False)]

    elif main_cat == "Campionato Singolo Domestico":
        if single_choice == "Premier League":
            temp = temp[temp["league_text"].str.contains("premier", na=False) & ~temp["league_text"].str.contains("scotland|premiership|spfl|scottish", na=False)]
        elif single_choice == "Bundesliga (1. Divisione)":
            temp = temp[temp["league_text"].str.contains("bundesliga", na=False) & ~temp["league_text"].str.contains("bundesliga-2|2-bundesliga|2. bundesliga|austria", na=False)]
        elif single_choice == "Scottish Premiership":
            temp = temp[temp["league_text"].str.contains("scotland|premiership|spfl|scottish", na=False)]
        elif single_choice == "Liga Portugal":
            temp = temp[temp["league_text"].str.contains("portugal|primeira|betclic", na=False)]
        elif single_choice == "LaLiga EA Sports":
            temp = temp[temp["league_text"].str.contains("laliga|spain|santander", na=False) & ~temp["league_text"].str.contains("segunda", na=False)]
        elif single_choice == "Ligue 1":
            temp = temp[temp["league_text"].str.contains("ligue 1|ligue-1", na=False) & ~temp["league_text"].str.contains("ligue-2|ligue 2", na=False)]
        elif single_choice == "Eredivisie":
            temp = temp[temp["league_text"].str.contains("eredivisie|netherlands", na=False)]
        elif single_choice == "Jupiler Pro League":
            temp = temp[temp["league_text"].str.contains("jupiler|belgium", na=False)]
        elif single_choice == "MLS":
            temp = temp[temp["league_text"].str.contains("mls|major league soccer", na=False)]

    elif main_cat == "All-Star (Tutti i campionati)":
        pass
        
    return temp

eligible_df = filter_eligible_cards(df, comp_type, selected_competition, single_league_choice)

tab_builder, tab_h2h, tab_gallery = st.tabs(["🏆 Builder Formazione", "⚔️ Head-to-Head (1v1)", "📊 Rosa Limited"])

# --- TAB 1: BUILDER ---
with tab_builder:
    st.subheader(f"Composizione: {selected_competition}")
    
    is_so7 = ("SO7" in selected_competition)
    slots_needed = ["GK", "DEF 1", "DEF 2", "MID 1", "MID 2", "FWD", "EXTRA"] if is_so7 else ["GK", "DEF", "MID", "FWD", "EXTRA"]
    
    st.caption(f"Formato: **{'SO7 (7 Titolari Classic)' if is_so7 else 'SO5 (In-Season: Min 4 In-Season + Max 1 Classic)'}** — Carte Limited disponibili: **{len(eligible_df)}**")
    
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
                    f"{row['name']} ({row['club_name']}) - {'🟢' if row['is_in_season'] else '⚪'} (+{row['bonus_pct']}%) - {row['position']} - L5: {row['l5_apps']}/5": row['card_slug']
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
            st.write("##### Monitoraggio Punteggi Attesi (Con Bonus Reali)")
            active_lineup = [c for c in selected_cards.values() if c is not None]
            
            if len(active_lineup) == len(slots_needed):
                if not is_so7:
                    classic_count = sum(1 for c in active_lineup if not c["is_in_season"])
                    in_season_count = sum(1 for c in active_lineup if c["is_in_season"])
                    
                    if classic_count > 1:
                        st.error(f"⚠️ **Regola Sorare Violata!** Hai inserito {classic_count} carte Classic. In modalità In-Season è consentita **al massimo 1 sola carta Classic** (minimo 4 In-Season).")
                    else:
                        st.success(f"✅ Requisito In-Season rispettato ({in_season_count} In-Season, {classic_count} Classic).")
                
                cap_candidate = max(active_lineup, key=lambda x: x["ceiling_idx"] * x["multiplier"])
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
    st.subheader("⚔️ Confronto Diretto Ballottaggi (Tutte le Versioni)")
    col1, col2 = st.columns(2)
    
    h2h_options = {
        f"{row['name']} ({row['club_name']}) - {'🟢 In-S' if row['is_in_season'] else '⚪ Classic'} (+{row['bonus_pct']}%) - {row['position']} - L5: {row['l5_apps']}/5 [id:{row['card_slug'][-6:]}]": row['card_slug']
        for _, row in df.iterrows()
    }
    
    if h2h_options:
        with col1:
            c1_key = st.selectbox("Seleziona Carta A", list(h2h_options.keys()), index=0)
            p1 = df[df["card_slug"] == h2h_options[c1_key]].iloc[0]
            st.markdown(f"### {p1['name']}")
            st.caption(f"Squadra: **{p1['club_name']}** ({p1['league_name']})")
            st.write(f"• **Ruolo:** `{p1['position']}`")
            st.write(f"• **Bonus Livello (1%/lvl):** +{p1['level_bonus']}% (Livello {p1['grade']})")
            st.write(f"• **Bonus Collezione Club:** +{p1['collection_bonus']}%")
            st.write(f"• **Bonus Stagionale:** {'+5.0% (In-Season 2026)' if p1['is_in_season'] else '+0.0% (Classic)'}")
            st.write(f"• **Bonus Totale Carta:** **+{p1['bonus_pct']}%** (Moltiplicatore x{p1['multiplier']:.3f})")
            st.write(f"• **Titolarità L5:** {p1['starter_rate']}% ({p1['l5_apps']}/5 presenze)")
            
            p1_floor = round(p1['floor_idx'] * p1['multiplier'], 1)
            p1_ceil = round(p1['ceiling_idx'] * p1['multiplier'], 1)
            st.metric("Floor Effettivo (Con Bonus)", f"{p1_floor} pt")
            st.metric("Ceiling Effettivo (Con Bonus)", f"{p1_ceil} pt")

        with col2:
            c2_key = st.selectbox("Seleziona Carta B", list(h2h_options.keys()), index=min(1, len(h2h_options)-1))
            p2 = df[df["card_slug"] == h2h_options[c2_key]].iloc[0]
            st.markdown(f"### {p2['name']}")
            st.caption(f"Squadra: **{p2['club_name']}** ({p2['league_name']})")
            st.write(f"• **Ruolo:** `{p2['position']}`")
            st.write(f"• **Bonus Livello (1%/lvl):** +{p2['level_bonus']}% (Livello {p2['grade']})")
            st.write(f"• **Bonus Collezione Club:** +{p2['collection_bonus']}%")
            st.write(f"• **Bonus Stagionale:** {'+5.0% (In-Season 2026)' if p2['is_in_season'] else '+0.0% (Classic)'}")
            st.write(f"• **Bonus Totale Carta:** **+{p2['bonus_pct']}%** (Moltiplicatore x{p2['multiplier']:.3f})")
            st.write(f"• **Titolarità L5:** {p2['starter_rate']}% ({p2['l5_apps']}/5 presenze)")
            
            p2_floor = round(p2['floor_idx'] * p2['multiplier'], 1)
            p2_ceil = round(p2['ceiling_idx'] * p2['multiplier'], 1)
            st.metric("Floor Effettivo (Con Bonus)", f"{p2_floor} pt")
            st.metric("Ceiling Effettivo (Con Bonus)", f"{p2_ceil} pt")

# --- TAB 3: ROSA GENERALE ---
with tab_gallery:
    st.subheader("📊 Rosa Ufficiale Limited (Solo Carte Limited)")
    display_df = df[["name", "club_name", "league_name", "position", "is_in_season", "grade", "level_bonus", "collection_bonus", "season_bonus", "bonus_pct", "multiplier", "floor_idx", "ceiling_idx", "card_slug"]].copy()
    display_df["is_in_season"] = display_df["is_in_season"].apply(lambda x: "🟢 In-Season (2026)" if x else "⚪ Classic")
    display_df["grade"] = display_df["grade"].apply(lambda x: f"Lvl {x}")
    display_df["level_bonus"] = display_df["level_bonus"].apply(lambda x: f"+{x}%")
    display_df["collection_bonus"] = display_df["collection_bonus"].apply(lambda x: f"+{x}%")
    display_df["season_bonus"] = display_df["season_bonus"].apply(lambda x: f"+{x}%")
    display_df["bonus_pct"] = display_df["bonus_pct"].apply(lambda x: f"+{x}%")
    display_df["is_locked"] = display_df["card_slug"].apply(lambda x: "🔒 Schierato" if x in st.session_state["locked_cards"] else "🟢 Libero")
    
    st.dataframe(
        display_df,
        column_config={
            "name": "Calciatore",
            "club_name": "Club Collezione",
            "league_name": "Campionato",
            "position": "Ruolo",
            "is_in_season": "Stagionalità",
            "grade": "Livello XP",
            "level_bonus": "Bonus XP (1%/lvl)",
            "collection_bonus": "Bonus Collezione",
            "season_bonus": "Bonus Stagionale",
            "bonus_pct": "Bonus Totale Carta",
            "multiplier": "Moltiplicatore",
            "floor_idx": "Floor Base",
            "ceiling_idx": "Ceiling Base",
            "is_locked": "Stato GW"
        },
        use_container_width=True,
        hide_index=True
    )
