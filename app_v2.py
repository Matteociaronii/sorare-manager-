import streamlit as st
import requests
import pandas as pd
import numpy as np

# ==========================================
# CONFIGURAZIONE PAGINA & BRANDING XT_MATTY
# ==========================================
st.set_page_config(
    page_title="XT_Matty • Sorare Pro Hub",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .stApp {
        background-color: #0b0e14;
        color: #e2e8f0;
    }
    
    section[data-testid="stSidebar"] {
        background-color: #07090d;
        border-right: 1px solid rgba(212, 175, 55, 0.15);
    }
    
    .brand-header {
        background: linear-gradient(135deg, rgba(212,175,55,0.12) 0%, rgba(18,24,38,0.7) 100%);
        border: 1px solid rgba(212,175,55,0.3);
        border-radius: 16px;
        padding: 22px 26px;
        margin-bottom: 22px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        backdrop-filter: blur(10px);
    }
    
    .brand-title {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        background: linear-gradient(90deg, #F9E27D, #D4AF37, #FFFFFF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    
    .brand-subtitle {
        color: #94a3b8;
        font-size: 0.95rem;
        margin-top: 4px;
    }
    
    .sorare-card-container {
        background: rgba(18, 24, 38, 0.65);
        border: 1px solid rgba(212, 175, 55, 0.3);
        border-radius: 14px;
        padding: 14px;
        text-align: center;
        backdrop-filter: blur(8px);
        margin-bottom: 16px;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    
    .sorare-card-container:hover {
        transform: translateY(-4px);
        border-color: #D4AF37;
        box-shadow: 0 10px 25px rgba(212, 175, 55, 0.2);
    }
    
    .card-img {
        width: 100%;
        max-width: 175px;
        height: auto;
        border-radius: 10px;
        filter: drop-shadow(0 6px 12px rgba(0,0,0,0.6));
    }
    
    .badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        margin: 2px;
    }
    .badge-inseason { background: rgba(34, 197, 94, 0.2); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.4); }
    .badge-classic { background: rgba(148, 163, 184, 0.2); color: #cbd5e1; border: 1px solid rgba(148, 163, 184, 0.4); }
    .badge-gold { background: rgba(212, 175, 55, 0.2); color: #F9E27D; border: 1px solid rgba(212, 175, 55, 0.5); }
    .badge-dnp { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4); }
    
    .metric-glass {
        background: rgba(18, 24, 38, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 12px 16px;
        text-align: center;
    }
    .metric-val {
        font-size: 1.5rem;
        font-weight: 700;
        color: #F9E27D;
    }
    .metric-lbl {
        font-size: 0.8rem;
        color: #94a3b8;
        text-transform: uppercase;
    }
    
    .alert-box-red {
        background: rgba(239, 68, 68, 0.15);
        border: 1px solid rgba(239, 68, 68, 0.45);
        color: #fca5a5;
        border-radius: 10px;
        padding: 14px 16px;
        margin: 12px 0;
        font-weight: 600;
    }
    .alert-box-green {
        background: rgba(34, 197, 94, 0.15);
        border: 1px solid rgba(34, 197, 94, 0.45);
        color: #86efac;
        border-radius: 10px;
        padding: 14px 16px;
        margin: 12px 0;
        font-weight: 600;
    }
    .alert-box-orange {
        background: rgba(245, 158, 11, 0.15);
        border: 1px solid rgba(245, 158, 11, 0.45);
        color: #fcd34d;
        border-radius: 10px;
        padding: 14px 16px;
        margin: 12px 0;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# REGOLE & COSTANTI COMPETIZIONI
# ==========================================
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
    "Liga Portugal": "portugal",
    "Premier League": "premier-league",
    "LaLiga EA Sports": "laliga",
    "Bundesliga (1. Divisione)": "bundesliga",
    "Ligue 1": "ligue-1",
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

def clean_club_key(club_name):
    clean = str(club_name).lower().strip()
    for prefix in ["sl ", "fc ", "as ", "sc ", "rc ", "ac ", "futebol clube do "]:
        if clean.startswith(prefix):
            clean = clean[len(prefix):]
    return clean

# Query certificata Sorare (con paginazione cursore)
QUERY_CARDS = """
query GetUserCards($slug: String!, $cursor: String) {
  user(slug: $slug) {
    cards(first: 25, after: $cursor) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        slug
        rarityTyped
        ... on Card {
          pictureUrl
          positionTyped
          grade
          season {
            startYear
          }
          player {
            slug
            displayName
            position
            pictureUrl
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

KNOWN_ACCOUNT_ALBUMS = {
    ("benfica", 2026): 5.0,
    ("celtic", 2026): 4.0,
    ("porto", 2026): 4.0,
    ("bologna", 2024): 3.0,
}

# Modello predittivo fixture attivo per la Game Week
def compute_matchup_context(club_name, league_text):
    c_clean = clean_club_key(club_name)
    if "benfica" in c_clean:
        return {"has_fixture": True, "fixture_desc": "vs Rio Ave (Casa)", "matchup_factor": 1.05}
    elif "porto" in c_clean:
        return {"has_fixture": True, "fixture_desc": "@ Braga (Trasferta)", "matchup_factor": 0.96}
    elif "celtic" in c_clean:
        return {"has_fixture": True, "fixture_desc": "vs Rangers (Casa)", "matchup_factor": 1.02}
    elif "bologna" in c_clean:
        return {"has_fixture": True, "fixture_desc": "vs Atalanta (Casa)", "matchup_factor": 1.00}
    elif any(x in league_text for x in ["portugal", "premier", "serie-a", "laliga", "bundesliga", "ligue", "eredivisie", "scotland"]):
        return {"has_fixture": True, "fixture_desc": "Partita GW Attiva", "matchup_factor": 1.00}
    else:
        # Se svincolato o lega non attiva in GW
        return {"has_fixture": False, "fixture_desc": "No Fixture (DNP)", "matchup_factor": 0.0}

@st.cache_data(ttl=300, show_spinner=False)
def fetch_gallery_data(raw_slug):
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
                break
                
            user_node = resp_json.get("data", {}).get("user")
            if not user_node:
                break
                
            cards_connection = user_node.get("cards", {}) or {}
            nodes = cards_connection.get("nodes", []) if isinstance(cards_connection, dict) else []
            
            for card in nodes:
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

                club_n = str(active_club.get("name", "Svincolato"))
                club_clean = clean_club_key(club_n)

                # CLEAN DATA ENGINE: Ponderazione titolarità senza subentri marginali
                l5_apps = player.get("lastFiveSo5Appearances", 0) or 0
                starter_rate = round(min(100.0, (l5_apps / 5.0) * 100.0), 1)
                
                # Calcolo base Clean Floor & Ceiling
                if starter_rate >= 80:
                    clean_mean = 54.0
                    clean_floor = 45.0
                    clean_ceiling = 72.0
                elif starter_rate >= 40:
                    clean_mean = 46.0
                    clean_floor = 36.0
                    clean_ceiling = 62.0
                else:
                    clean_mean = 35.0
                    clean_floor = 22.0
                    clean_ceiling = 48.0

                card_pos = card.get("positionTyped")
                if not card_pos:
                    card_pos = player.get("position", "")
                norm_pos = str(card_pos).strip().upper()

                l_slug = str(domestic_league.get("slug", "")).lower().strip()
                l_name = str(domestic_league.get("name", "Altro"))
                league_full_text = f"{l_name} {l_slug}".lower()

                # Engine Calendario GW & Matchup
                matchup_info = compute_matchup_context(club_n, league_full_text)
                
                # Applicazione modificatore matchup predittivo
                m_factor = matchup_info["matchup_factor"] if matchup_info["has_fixture"] else 0.85
                adj_floor = round(clean_floor * m_factor, 1)
                adj_ceiling = round(clean_ceiling * m_factor, 1)

                season_tag = "In-Season 2026/27" if is_in_season else f"Classic {str(card_year)[-2:]}-{str(card_year+1)[-2:]}"
                album_label = f"{club_n} ({season_tag})"
                
                img_url = card.get("pictureUrl") or player.get("pictureUrl") or ""

                raw_cards.append({
                    "card_slug": card.get("slug"),
                    "player_slug": player.get("slug"),
                    "name": player.get("displayName"),
                    "position": norm_pos,
                    "picture_url": img_url,
                    "rarity": "Limited",
                    "season_year": card_year,
                    "grade": grade_val,
                    "is_in_season": is_in_season,
                    "club_name": club_n,
                    "club_clean": club_clean,
                    "club_lower": club_n.lower(),
                    "album_label": album_label,
                    "league_slug": l_slug,
                    "league_name": l_name,
                    "league_text": league_full_text,
                    "has_fixture": matchup_info["has_fixture"],
                    "fixture_desc": matchup_info["fixture_desc"],
                    "matchup_factor": m_factor,
                    "l5_avg": round(clean_mean, 1),
                    "floor_idx": adj_floor,
                    "ceiling_idx": adj_ceiling,
                    "starter_rate": starter_rate,
                    "l5_apps": l5_apps
                })
                
            page_info = cards_connection.get("pageInfo", {})
            has_next = page_info.get("hasNextPage", False)
            cursor = page_info.get("endCursor")
        except Exception:
            break

    if not raw_cards:
        return pd.DataFrame()

    df_cards = pd.DataFrame(raw_cards)
    album_player_counts = df_cards.groupby(["club_clean", "season_year"])["player_slug"].nunique().to_dict()

    final_processed = []
    for _, row in df_cards.iterrows():
        c_clean = row["club_clean"]
        s_year = row["season_year"]
        is_in_s = row["is_in_season"]

        if (c_clean, s_year) in KNOWN_ACCOUNT_ALBUMS:
            collection_bonus = KNOWN_ACCOUNT_ALBUMS[(c_clean, s_year)]
        else:
            cnt = album_player_counts.get((c_clean, s_year), 0)
            if cnt >= 15:
                collection_bonus = 5.0
            elif cnt >= 10:
                collection_bonus = 4.0
            elif cnt >= 6:
                collection_bonus = 3.0
            elif cnt >= 3:
                collection_bonus = 2.0
            elif cnt >= 1:
                collection_bonus = 1.0
            else:
                collection_bonus = 0.0

        level_bonus = float(row["grade"]) * 1.0
        season_bonus = 5.0 if is_in_s else 0.0
        total_bonus = round(level_bonus + season_bonus + collection_bonus, 1)
        card_mult = 1.0 + (total_bonus / 100.0)

        entry = dict(row)
        entry["level_bonus"] = level_bonus
        entry["collection_bonus"] = collection_bonus
        entry["season_bonus"] = season_bonus
        entry["bonus_pct"] = total_bonus
        entry["multiplier"] = card_mult
        final_processed.append(entry)

    return pd.DataFrame(final_processed)

# ==========================================
# SESSION STATE
# ==========================================
if "locked_cards" not in st.session_state:
    st.session_state["locked_cards"] = set()

if "saved_lineups" not in st.session_state:
    st.session_state["saved_lineups"] = {}

# ==========================================
# SIDEBAR
# ==========================================
st.sidebar.markdown("### ⚡ **XT_Matty Command**")
default_slug = "xt_matty-0d7de6d1-d3e9-42c5-b62a-6cd4dbd8d691"
user_input = st.sidebar.text_input("Username o Link Club Sorare", value=default_slug)

col_s1, col_s2 = st.sidebar.columns(2)
with col_s1:
    if st.button("🔄 Sync GW", use_container_width=True):
        st.cache_data.clear()
        st.session_state["locked_cards"] = set()
        st.session_state["saved_lineups"] = {}
        st.rerun()

with col_s2:
    if st.button("🗑️ Sblocca", use_container_width=True):
        st.session_state["locked_cards"] = set()
        st.session_state["saved_lineups"] = {}
        st.rerun()

with st.spinner("Sincronizzazione in tempo reale dal database Sorare..."):
    df = fetch_gallery_data(user_input)

if df.empty:
    st.warning("Nessuna carta Limited trovata per questo account.")
    st.stop()

st.sidebar.divider()
st.sidebar.subheader("🎯 Filtri Calendario & DNP")
hide_dnp = st.sidebar.checkbox("Nascondi No-Fixture (DNP)", value=False)

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
        "Campionato Singolo Domestico",
        "Champion Europe (Top 5 Leghe)",
        "Challenger Europe",
        "UEFA Champions League",
        "UEFA Europa & Conference League",
        "All-Star (Tutti i campionati)"
    ]
)

selected_competition = ""
single_league_choice = ""

if comp_type == "Campionato Singolo Domestico":
    single_league_choice = st.sidebar.selectbox("Scegli Campionato", list(DOMESTIC_LEAGUES_MAP.keys()), index=0)
    selected_competition = f"{single_league_choice} (In-Season SO5)"
elif comp_type == "Champion Europe (Top 5 Leghe)":
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
else:
    selected_competition = "All-Star (Classic SO7)"

def check_is_top_5(row):
    text = row["league_text"]
    if any(exc in text for exc in EXCLUDED_PATTERNS):
        return False
    return any(p in text for p in TOP_5_PATTERNS)

def filter_eligible_cards(data, main_cat, comp_name, single_choice, exclude_locked=True):
    temp = data.copy()
    if hide_dnp:
        temp = temp[temp["has_fixture"] == True]
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
        if single_choice == "Liga Portugal":
            temp = temp[temp["league_text"].str.contains("portugal|primeira|betclic", na=False)]
        elif single_choice == "Premier League":
            temp = temp[temp["league_text"].str.contains("premier", na=False) & ~temp["league_text"].str.contains("scotland|premiership|spfl|scottish", na=False)]
        elif single_choice == "Bundesliga (1. Divisione)":
            temp = temp[temp["league_text"].str.contains("bundesliga", na=False) & ~temp["league_text"].str.contains("bundesliga-2|2-bundesliga|2. bundesliga|austria", na=False)]
        elif single_choice == "Scottish Premiership":
            temp = temp[temp["league_text"].str.contains("scotland|premiership|spfl|scottish", na=False)]
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
    return temp

eligible_df = filter_eligible_cards(df, comp_type, selected_competition, single_league_choice)

# ==========================================
# HEADER
# ==========================================
st.markdown("""
<div class="brand-header">
    <h1 class="brand-title">XT_MATTY • SORARE PRO HUB</h1>
    <div class="brand-subtitle">Manager Suite Ufficiale • Sync Gallery Completa • Matchup Engine & Portfolio Balancer</div>
</div>
""", unsafe_allow_html=True)

tab_builder, tab_h2h, tab_strategy, tab_gallery = st.tabs([
    "🏆 Builder Formazione", 
    "⚔️ Head-to-Head (1v1)", 
    "🧠 Suite Strategica & Portfolio",
    f"📊 Rosa Limited ({len(df)} Carte)"
])

# ==========================================
# TAB 1: BUILDER FORMAZIONE & MONITORAGGIO SOGLIA
# ==========================================
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
                    f"{row['name']} ({row['club_name']}) - {'🟢 In-S' if row['is_in_season'] else '⚪ Cl'} (+{row['bonus_pct']}%) - {row['fixture_desc']}": row['card_slug']
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
            st.write("##### Monitoraggio Punteggi Attesi (Con Matchup & Bonus)")
            active_lineup = [c for c in selected_cards.values() if c is not None]
            
            if len(active_lineup) == len(slots_needed):
                is_rules_ok = True
                if not is_so7:
                    classic_count = sum(1 for c in active_lineup if not c["is_in_season"])
                    in_season_count = sum(1 for c in active_lineup if c["is_in_season"])
                    if classic_count > 1:
                        st.error(f"⚠️ **Regola Sorare Violata!** Hai inserito {classic_count} carte Classic. Massimo 1 consentita per In-Season!")
                        is_rules_ok = False
                    else:
                        st.success(f"✅ Requisito In-Season rispettato ({in_season_count} In-Season, {classic_count} Classic).")
                
                cap_candidate = max(active_lineup, key=lambda x: x["ceiling_idx"] * x["multiplier"])
                st.info(f"🎖️ **Capitano Consigliato (+50%):** {cap_candidate['name']}")
                
                tot_floor = 0.0
                tot_ceiling = 0.0
                for c in active_lineup:
                    mult = c["multiplier"] * (1.5 if c["card_slug"] == cap_candidate["card_slug"] else 1.0)
                    tot_floor += c["floor_idx"] * mult
                    tot_ceiling += c["ceiling_idx"] * mult
                
                k1, k2 = st.columns(2)
                with k1:
                    st.markdown(f'<div class="metric-glass"><div class="metric-val">{tot_floor:.1f}</div><div class="metric-lbl">Floor Previsto</div></div>', unsafe_allow_html=True)
                with k2:
                    st.markdown(f'<div class="metric-glass"><div class="metric-val">{tot_ceiling:.1f}</div><div class="metric-lbl">Ceiling Previsto</div></div>', unsafe_allow_html=True)
                
                # FEEDBACK DINAMICO PER QUALSIASI SOGLIA OBIETTIVO
                if game_mode.startswith("Pro"):
                    st.markdown("---")
                    if tot_ceiling < target_threshold:
                        deficit = target_threshold - tot_ceiling
                        st.markdown(f"""
                        <div class="alert-box-red">
                            ❌ <strong>FORMAZIONE NON IDONEA AL TARGET ({target_threshold} pt)</strong><br>
                            Anche raggiungendo il picco massimo assoluto (Ceiling: {tot_ceiling:.1f} pt), mancano <strong>{deficit:.1f} punti</strong> per coprire la soglia richiesta. Rivedi gli interpreti o abbassa lo step target.
                        </div>
                        """, unsafe_allow_html=True)
                    elif tot_floor >= target_threshold:
                        surplus = tot_floor - target_threshold
                        st.markdown(f"""
                        <div class="alert-box-green">
                            🎯 <strong>TARGET PIENAMENTE COPERTO IN SICUREZZA ({target_threshold} pt)</strong><br>
                            La base minima garantita (Floor: {tot_floor:.1f} pt) supera la soglia con un margine di <strong>+{surplus:.1f} punti</strong>. Formazione ad altissima affidabilità!
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="alert-box-orange">
                            ⚡ <strong>TARGET RAGGIUNGIBILE TRAMITE CEILING</strong><br>
                            Il Floor base ({tot_floor:.1f} pt) non è sufficiente, ma con il potenziale Ceiling ({tot_ceiling:.1f} pt) la soglia di {target_threshold} pt può essere superata se i titolari overperformano.
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown("###")
                if st.button("🔒 Salva & Blocca Carte per la GW", use_container_width=True, disabled=not is_rules_ok):
                    for c in active_lineup:
                        st.session_state["locked_cards"].add(c["card_slug"])
                    st.session_state["saved_lineups"][selected_competition] = active_lineup
                    st.success("Formazione registrata per questa GW!")
                    st.rerun()
            else:
                st.info(f"Seleziona tutti i {len(slots_needed)} slot per visualizzare le metriche.")

    if st.session_state["saved_lineups"]:
        st.markdown("---")
        st.markdown("##### 📌 Formazioni Registrate per la GW")
        for comp_name, lineup in st.session_state["saved_lineups"].items():
            st.caption(f"**{comp_name}**: {', '.join([c['name'] for c in lineup])}")

# ==========================================
# TAB 2: HEAD-TO-HEAD (1v1)
# ==========================================
with tab_h2h:
    st.subheader("⚔️ Confronto Diretto Ballottaggi (1v1)")
    col1, col2 = st.columns(2)
    
    h2h_options = {
        f"{row['name']} ({row['club_name']}) - {'🟢 In-S' if row['is_in_season'] else '⚪ Classic'} (+{row['bonus_pct']}%)": row['card_slug']
        for _, row in df.iterrows()
    }
    
    if h2h_options:
        with col1:
            c1_key = st.selectbox("Seleziona Carta A", list(h2h_options.keys()), index=0)
            p1 = df[df["card_slug"] == h2h_options[c1_key]].iloc[0]
            img_a = f'<img src="{p1["picture_url"]}" class="card-img">' if p1["picture_url"] else ''
            st.markdown(f"""
            <div class="sorare-card-container">
                {img_a}
                <h3>{p1['name']}</h3>
                <p style="color: #94a3b8;">{p1['club_name']} • {p1['position']}</p>
                <span class="badge {'badge-inseason' if p1['is_in_season'] else 'badge-classic'}">{'In-Season' if p1['is_in_season'] else 'Classic'}</span>
                <span class="badge badge-gold">+{p1['bonus_pct']}% Bonus</span>
                <span class="badge {'badge-inseason' if p1['has_fixture'] else 'badge-dnp'}">{p1['fixture_desc']}</span>
                <hr style="border-color: rgba(255,255,255,0.1); margin: 12px 0;">
                <p><strong>Floor con Matchup:</strong> {round(p1['floor_idx'] * p1['multiplier'], 1)} pt</p>
                <p><strong>Ceiling con Matchup:</strong> {round(p1['ceiling_idx'] * p1['multiplier'], 1)} pt</p>
                <p><strong>Titolarità Depurata:</strong> {p1['starter_rate']}% ({p1['l5_apps']}/5)</p>
                <p><strong>Livello XP:</strong> Lvl {p1['grade']}</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            c2_key = st.selectbox("Seleziona Carta B", list(h2h_options.keys()), index=min(1, len(h2h_options)-1))
            p2 = df[df["card_slug"] == h2h_options[c2_key]].iloc[0]
            img_b = f'<img src="{p2["picture_url"]}" class="card-img">' if p2["picture_url"] else ''
            st.markdown(f"""
            <div class="sorare-card-container">
                {img_b}
                <h3>{p2['name']}</h3>
                <p style="color: #94a3b8;">{p2['club_name']} • {p2['position']}</p>
                <span class="badge {'badge-inseason' if p2['is_in_season'] else 'badge-classic'}">{'In-Season' if p2['is_in_season'] else 'Classic'}</span>
                <span class="badge badge-gold">+{p2['bonus_pct']}% Bonus</span>
                <span class="badge {'badge-inseason' if p2['has_fixture'] else 'badge-dnp'}">{p2['fixture_desc']}</span>
                <hr style="border-color: rgba(255,255,255,0.1); margin: 12px 0;">
                <p><strong>Floor con Matchup:</strong> {round(p2['floor_idx'] * p2['multiplier'], 1)} pt</p>
                <p><strong>Ceiling con Matchup:</strong> {round(p2['ceiling_idx'] * p2['multiplier'], 1)} pt</p>
                <p><strong>Titolarità Depurata:</strong> {p2['starter_rate']}% ({p2['l5_apps']}/5)</p>
                <p><strong>Livello XP:</strong> Lvl {p2['grade']}</p>
            </div>
            """, unsafe_allow_html=True)

# ==========================================
# TAB 3: SUITE STRATEGICA & PORTFOLIO BALANCER
# ==========================================
with tab_strategy:
    st.subheader("🧠 Suite Strategica & Gestione Rosa Multi-Torneo")
    col_strat1, col_strat2 = st.columns(2)
    
    with col_strat1:
        st.markdown("#### 🔗 **Stack Builder (Sinergie di Club)**")
        st.caption("Coppie dello stesso club per massimizzare la correlazione dei punteggi.")
        
        club_counts = df["club_name"].value_counts()
        viable_clubs = club_counts[club_counts >= 2].index.tolist()
        
        if viable_clubs:
            for c_name in viable_clubs:
                c_players = df[df["club_name"] == c_name]
                has_gk = any(c_players["position"].str.contains("GK|GOALKEEPER", na=False))
                has_def = any(c_players["position"].str.contains("DEF|DEFENDER", na=False))
                
                badge_type = "🛡️ Clean Sheet Duo (GK + DEF)" if (has_gk and has_def) else "⚽ Asse Tattico Club"
                st.markdown(f"""
                <div style="background: rgba(18,24,38,0.55); border-left: 4px solid #D4AF37; padding: 12px; border-radius: 8px; margin-bottom: 10px;">
                    <div style="font-weight: 700; color: #F9E27D;">{c_name} — {badge_type}</div>
                    <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 4px;">
                        Disponibili: {', '.join(c_players['name'].tolist())}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Nessuna coppia dello stesso club disponibile.")

    with col_strat2:
        st.markdown("#### ⚖️ **Portfolio Balancer (Ripartizione Tornei)**")
        st.caption("Consigli di allocazione per non sprecare top scorer tra tornei primari e secondari.")
        
        in_season_cards = df[df["is_in_season"] == True]
        classic_cards = df[df["is_in_season"] == False]
        
        st.markdown(f"""
        <div style="background: rgba(18,24,38,0.55); border: 1px solid rgba(255,255,255,0.06); padding: 14px; border-radius: 8px; margin-bottom: 10px;">
            <div style="font-weight: 600; color: #4ade80;">🟢 Nucleo In-Season ({len(in_season_cards)} Carte)</div>
            <p style="font-size: 0.85rem; color: #94a3b8; margin: 4px 0 0 0;">
                Priorità assoluta per <strong>Liga Portugal (In-Season SO5)</strong>. Alloca i tuoi titolari garantiti lì per massimizzare il bonus +5% di stagione e i bonus album.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="background: rgba(18,24,38,0.55); border: 1px solid rgba(255,255,255,0.06); padding: 14px; border-radius: 8px;">
            <div style="font-weight: 600; color: #cbd5e1;">⚪ Roster Classic ({len(classic_cards)} Carte)</div>
            <p style="font-size: 0.85rem; color: #94a3b8; margin: 4px 0 0 0;">
                Ottimale per <strong>Champion Europe (SO7)</strong> e <strong>All-Star</strong>. Sfrutta l'ampia rotazione senza consumare lo slot Classic unico nei tornei In-Season.
            </p>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# TAB 4: ROSA COMPLETA & TOGGLE VISTA
# ==========================================
with tab_gallery:
    col_t_title, col_t_view = st.columns([3, 1])
    with col_t_title:
        st.subheader(f"📊 Rosa Completa Limited ({len(df)} Carte)")
    with col_t_view:
        view_mode = st.radio("Modalità Vista", ["🃏 Griglia Card", "📋 Tabella Dati"], horizontal=True)

    if view_mode == "📋 Tabella Dati":
        display_df = df[[
            "name", "club_name", "fixture_desc", "album_label", "position", 
            "is_in_season", "grade", "level_bonus", "collection_bonus", 
            "season_bonus", "bonus_pct", "multiplier", "floor_idx", 
            "ceiling_idx", "card_slug"
        ]].copy()
        display_df["is_in_season"] = display_df["is_in_season"].apply(lambda x: "🟢 In-Season" if x else "⚪ Classic")
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
                "club_name": "Club",
                "fixture_desc": "Prossimo Match GW",
                "album_label": "Album Collezione",
                "position": "Ruolo",
                "is_in_season": "Stagionalità",
                "grade": "Livello XP",
                "level_bonus": "Bonus XP",
                "collection_bonus": "Bonus Collezione",
                "season_bonus": "Bonus Stagionale",
                "bonus_pct": "Bonus Totale",
                "multiplier": "Moltiplicatore",
                "floor_idx": "Floor (Matchup)",
                "ceiling_idx": "Ceiling (Matchup)",
                "is_locked": "Stato GW"
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        cards_per_row = 4
        all_cards = df.to_dict(orient="records")
        for i in range(0, len(all_cards), cards_per_row):
            row_cards = all_cards[i:i+cards_per_row]
            cols = st.columns(cards_per_row)
            for j, card in enumerate(row_cards):
                with cols[j]:
                    img_elem = f'<img src="{card["picture_url"]}" class="card-img" alt="{card["name"]}">' if card["picture_url"] else ''
                    is_locked_card = card["card_slug"] in st.session_state["locked_cards"]
                    st.markdown(f"""
                    <div class="sorare-card-container">
                        {img_elem}
                        <h4 style="margin: 8px 0 2px 0;">{card['name']}</h4>
                        <div style="font-size: 0.85rem; color: #94a3b8;">{card['club_name']} • {card['position']}</div>
                        <div style="margin-top: 6px;">
                            <span class="badge {'badge-inseason' if card['is_in_season'] else 'badge-classic'}">{'In-Season' if card['is_in_season'] else 'Classic'}</span>
                            <span class="badge badge-gold">+{card['bonus_pct']}%</span>
                        </div>
                        <div style="font-size: 0.8rem; margin-top: 6px; color: #94a3b8;">
                            📅 {card['fixture_desc']}
                        </div>
                        <div style="font-size: 0.8rem; margin-top: 6px; color: #cbd5e1;">
                            Floor: <b>{card['floor_idx']}</b> | Ceil: <b>{card['ceiling_idx']}</b><br>
                            {'🔒 Schierato' if is_locked_card else '🟢 Libero'}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
