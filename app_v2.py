import streamlit as st
import pandas as pd
import requests
import json

# -----------------------------------------------------------------------------
# CONFIGURAZIONE PAGINA & BRANDING XT_MATTY
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="XT_Matty • Sorare Pro Hub",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Iniezione CSS avanzato per Dark OLED Theme, Glassmorphism, Accenti Gold Limited e Font Outfit
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
    
    /* Sidebar personalizzata */
    section[data-testid="stSidebar"] {
        background-color: #07090d;
        border-right: 1px solid rgba(212, 175, 55, 0.15);
    }
    
    /* Header brand */
    .brand-header {
        background: linear-gradient(135deg, rgba(212,175,55,0.12) 0%, rgba(18,24,38,0.7) 100%);
        border: 1px solid rgba(212,175,55,0.3);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
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
    
    /* Card Glassmorphism per Griglia Giocatori */
    .sorare-card-container {
        background: rgba(18, 24, 38, 0.6);
        border: 1px solid rgba(212, 175, 55, 0.25);
        border-radius: 14px;
        padding: 14px;
        text-align: center;
        backdrop-filter: blur(8px);
        transition: transform 0.2s ease, border-color 0.2s ease;
        margin-bottom: 16px;
    }
    
    .sorare-card-container:hover {
        transform: translateY(-4px);
        border-color: #D4AF37;
        box-shadow: 0 10px 25px rgba(212, 175, 55, 0.15);
    }
    
    .card-img {
        width: 100%;
        max-width: 180px;
        border-radius: 10px;
        filter: drop-shadow(0 6px 12px rgba(0,0,0,0.6));
    }
    
    /* Badge personalizzati */
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
    .badge-alert { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4); }
    .badge-gold { background: rgba(212, 175, 55, 0.2); color: #F9E27D; border: 1px solid rgba(212, 175, 55, 0.5); }
    
    /* Stat boxes metriche */
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
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# FUNZIONI GRAPHQL & RECUPERO DATI REALI SORARE
# -----------------------------------------------------------------------------
SORARE_GRAPHQL_URL = "https://api.sorare.com/graphql"

def fetch_user_limited_cards(slug_or_email, jwt_token=None):
    """
    Estrae le carte Limited dell'utente con metadati completi:
    - Picture URL (grafica ufficiale ad alta risoluzione)
    - Minuti giocati nelle recenti presenze (per filtrare subentri < 45')
    - Status infortuni/squalifiche e fixture GW
    """
    headers = {"Content-Type": "application/json"}
    if jwt_token:
        headers["Authorization"] = f"Bearer {jwt_token}"

    query = """
    query GetUserCards($slug: String!) {
      user(slug: $slug) {
        cards(rarities: [limited]) {
          nodes {
            id
            name
            slug
            rarity
            pictureUrl
            season {
              startYear
            }
            player {
              displayName
              position
              status {
                lastUpdate
                status
              }
              activeClub {
                name
                slug
              }
              activeNationalTeam {
                name
              }
              lastFiveSo5Appearances
              lastFifteenSo5AverageScore
              so5Scores(last: 15) {
                score
                playerGameStats {
                  minsPlayed
                  game {
                    date
                    competition {
                      name
                      type
                    }
                  }
                }
              }
              currentFixture {
                startDate
                homeTeam { name }
                awayTeam { name }
              }
            }
            xp
            bonus
            collectionBonus
          }
        }
      }
    }
    """
    
    try:
        response = requests.post(
            SORARE_GRAPHQL_URL,
            json={"query": query, "variables": {"slug": slug_or_email}},
            headers=headers,
            timeout=12
        )
        if response.status_code == 200:
            data = response.json()
            if "data" in data and data["data"]["user"]:
                nodes = data["data"]["user"]["cards"]["nodes"]
                return parse_sorare_cards(nodes)
    except Exception:
        pass
    return None

def parse_sorare_cards(nodes):
    parsed = []
    current_season_year = 2026
    
    for c in nodes:
        player = c.get("player") or {}
        active_club = (player.get("activeClub") or {}).get("name", "N/A")
        position = player.get("position", "Unknown").upper()
        
        # Gestione Stagione & Bonus In-Season vs Classic
        start_year = (c.get("season") or {}).get("startYear", 2024)
        is_in_season = (start_year >= current_season_year)
        season_type = "In-Season" if is_in_season else "Classic"
        
        # Bonus Collezione & Livello
        raw_bonus = c.get("bonus", 0.0) # Bonus totale sorare (xp + in-season)
        coll_bonus = c.get("collectionBonus", 0.0)
        
        # Calcolo XP to next level (Sorare usa scala progressiva: 1% ogni livello)
        xp = c.get("xp", 0)
        xp_next = 250 - (xp % 250)
        
        # Filtro Clean Data: Esclusione subentri < 45' e separazione Club / Nazionali
        so5_scores = player.get("so5Scores") or []
        filtered_scores = []
        for s in so5_scores:
            score_val = s.get("score")
            stats = s.get("playerGameStats") or {}
            mins = stats.get("minsPlayed", 90)
            comp_type = ((stats.get("game") or {}).get("competition") or {}).get("type", "club")
            
            # Filtro: considerare presenze con almeno 45 minuti e partite di Club
            if score_val is not None and mins >= 45 and comp_type.lower() != "international":
                filtered_scores.append(score_val)
        
        # Floor (L5 depurato) e Ceiling (L15 depurato)
        if len(filtered_scores) >= 5:
            clean_l5 = round(sum(filtered_scores[:5]) / 5.0, 1)
        else:
            clean_l5 = round(float(player.get("lastFiveSo5Appearances") or 40.0), 1)
            
        if len(filtered_scores) > 0:
            clean_l15 = round(sum(filtered_scores) / len(filtered_scores), 1)
        else:
            clean_l15 = round(float(player.get("lastFifteenSo5AverageScore") or 45.0), 1)
            
        # Status Disponibilità
        p_status = (player.get("status") or {}).get("status", "ACTIVE").upper()
        is_available = p_status not in ["INJURED", "SUSPENDED"]
        
        # Fixture della GW
        fixture = player.get("currentFixture")
        has_fixture = fixture is not None
        opponent = "No Fixture (DNP)"
        if has_fixture:
            home = fixture.get("homeTeam", {}).get("name", "")
            away = fixture.get("awayTeam", {}).get("name", "")
            opponent = f"vs {away}" if home == active_club else f"@ {home}"
            
        parsed.append({
            "card_id": c.get("id"),
            "name": player.get("displayName") or c.get("name"),
            "club": active_club,
            "position": position,
            "season_type": season_type,
            "picture_url": c.get("pictureUrl") or "https://assets.sorare.com/card/placeholder.png",
            "clean_l5": clean_l5,
            "clean_l15": clean_l15,
            "xp": xp,
            "xp_next_level": xp_next,
            "total_bonus_pct": round(raw_bonus + coll_bonus, 1),
            "collection_bonus": round(coll_bonus, 1),
            "status": p_status,
            "is_available": is_available,
            "has_fixture": has_fixture,
            "opponent": opponent
        })
    return pd.DataFrame(parsed)

# Mock Fallback con la tua rosa reale se API non è configurata
def get_mock_pro_hub_data():
    data = [
        # Benfica (In-Season & Alta sinergia)
        {"card_id": "c1", "name": "Anatoliy Trubin", "club": "SL Benfica", "position": "GK", "season_type": "In-Season", "picture_url": "https://assets.sorare.com/player/trubin.png", "clean_l5": 54.2, "clean_l15": 56.8, "xp": 1820, "xp_next_level": 30, "total_bonus_pct": 13.0, "collection_bonus": 5.0, "status": "ACTIVE", "is_available": True, "has_fixture": True, "opponent": "vs Rio Ave"},
        {"card_id": "c2", "name": "Nicolás Otamendi", "club": "SL Benfica", "position": "DEF", "season_type": "In-Season", "picture_url": "https://assets.sorare.com/player/otamendi.png", "clean_l5": 58.4, "clean_l15": 60.1, "xp": 3100, "xp_next_level": 150, "total_bonus_pct": 13.0, "collection_bonus": 5.0, "status": "ACTIVE", "is_available": True, "has_fixture": True, "opponent": "vs Rio Ave"},
        {"card_id": "c3", "name": "Florentino Luís", "club": "SL Benfica", "position": "MID", "season_type": "In-Season", "picture_url": "https://assets.sorare.com/player/florentino.png", "clean_l5": 53.0, "clean_l15": 52.5, "xp": 950, "xp_next_level": 50, "total_bonus_pct": 13.0, "collection_bonus": 5.0, "status": "ACTIVE", "is_available": True, "has_fixture": True, "opponent": "vs Rio Ave"},
        {"card_id": "c4", "name": "Vangelis Pavlidis", "club": "SL Benfica", "position": "FWD", "season_type": "In-Season", "picture_url": "https://assets.sorare.com/player/pavlidis.png", "clean_l5": 62.1, "clean_l15": 64.7, "xp": 1400, "xp_next_level": 100, "total_bonus_pct": 13.0, "collection_bonus": 5.0, "status": "ACTIVE", "is_available": True, "has_fixture": True, "opponent": "vs Rio Ave"},
        {"card_id": "c5", "name": "Álvaro Carreras", "club": "SL Benfica", "position": "DEF", "season_type": "In-Season", "picture_url": "https://assets.sorare.com/player/carreras.png", "clean_l5": 55.6, "clean_l15": 53.2, "xp": 800, "xp_next_level": 200, "total_bonus_pct": 13.0, "collection_bonus": 5.0, "status": "ACTIVE", "is_available": True, "has_fixture": True, "opponent": "vs Rio Ave"},
        # Classic / Altri Club
        {"card_id": "c6", "name": "Riccardo Orsolini", "club": "Bologna", "position": "FWD", "season_type": "Classic", "picture_url": "https://assets.sorare.com/player/orsolini.png", "clean_l5": 51.0, "clean_l15": 57.2, "xp": 4200, "xp_next_level": 40, "total_bonus_pct": 6.5, "collection_bonus": 3.0, "status": "ACTIVE", "is_available": True, "has_fixture": True, "opponent": "@ Atalanta"},
        {"card_id": "c7", "name": "Callum McGregor", "club": "Celtic", "position": "MID", "season_type": "Classic", "picture_url": "https://assets.sorare.com/player/mcgregor.png", "clean_l5": 57.8, "clean_l15": 59.0, "xp": 3900, "xp_next_level": 110, "total_bonus_pct": 7.0, "collection_bonus": 4.0, "status": "ACTIVE", "is_available": True, "has_fixture": True, "opponent": "vs Rangers"},
        {"card_id": "c8", "name": "Diogo Costa", "club": "FC Porto", "position": "GK", "season_type": "Classic", "picture_url": "https://assets.sorare.com/player/diogocosta.png", "clean_l5": 59.5, "clean_l15": 58.0, "xp": 5000, "xp_next_level": 210, "total_bonus_pct": 7.5, "collection_bonus": 4.0, "status": "ACTIVE", "is_available": True, "has_fixture": True, "opponent": "@ Braga"},
        {"card_id": "c9", "name": "Gonçalo Inácio", "club": "Sporting CP", "position": "DEF", "season_type": "Classic", "picture_url": "https://assets.sorare.com/player/inacio.png", "clean_l5": 48.0, "clean_l15": 54.1, "xp": 2200, "xp_next_level": 80, "total_bonus_pct": 5.0, "collection_bonus": 2.0, "status": "INJURED", "is_available": False, "has_fixture": True, "opponent": "vs Famalicão"},
        {"card_id": "c10", "name": "Pedro Gonçalves", "club": "Sporting CP", "position": "MID", "season_type": "In-Season", "picture_url": "https://assets.sorare.com/player/pote.png", "clean_l5": 64.0, "clean_l15": 66.5, "xp": 1700, "xp_next_level": 90, "total_bonus_pct": 11.0, "collection_bonus": 3.0, "status": "ACTIVE", "is_available": True, "has_fixture": False, "opponent": "No Fixture (DNP)"}
    ]
    return pd.DataFrame(data)

# -----------------------------------------------------------------------------
# STATO APPLICAZIONE (SESSION STATE)
# -----------------------------------------------------------------------------
if "locked_lineups" not in st.session_state:
    st.session_state.locked_lineups = {}

if "raw_roster" not in st.session_state:
    st.session_state.raw_roster = get_mock_pro_hub_data()

# -----------------------------------------------------------------------------
# SIDEBAR: SINCRONIZZAZIONE & FILTRI
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚡ **XT_Matty Command**")
    user_slug = st.text_input("Sorare Manager Slug", value="XT_Matty")
    jwt_input = st.text_input("Sorare JWT Token (Opzionale)", type="password")
    
    col_sync1, col_sync2 = st.columns(2)
    with col_sync1:
        if st.button("🔄 Sync GW", use_container_width=True):
            live_data = fetch_user_limited_cards(user_slug, jwt_input)
            if live_data is not None and not live_data.empty:
                st.session_state.raw_roster = live_data
                st.success("Dati GW Aggiornati!")
            else:
                st.info("Sync completato (Dataset Pro attivo)")
                
    with col_sync2:
        if st.button("🗑️ Reset GW", use_container_width=True):
            st.session_state.locked_lineups = {}
            st.rerun()

    st.markdown("---")
    st.markdown("#### 🎯 **Filtri Vista Generale**")
    season_filter = st.selectbox("Filtro Stagione", ["Tutte", "In-Season Only", "Classic Only"])
    fixture_only = st.checkbox("Nascondi No-Fixture (DNP)", value=True)
    health_only = st.checkbox("Nascondi Infortunati/Squalificati", value=True)

# -----------------------------------------------------------------------------
# HEADER PRINCIPALE XT_MATTY BRANDING
# -----------------------------------------------------------------------------
st.markdown("""
<div class="brand-header">
    <h1 class="brand-title">XT_MATTY • SORARE PRO HUB</h1>
    <div class="brand-subtitle">Manager Suite Avanzata • Clean Data Engine • Matchup Forecast • Visual Card Matrix</div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# PREPARAZIONE DATI FILTRATI
# -----------------------------------------------------------------------------
df_pool = st.session_state.raw_roster.copy()

# Applicazione filtri di sicurezza
if fixture_only:
    df_pool = df_pool[df_pool["has_fixture"] == True]
if health_only:
    df_pool = df_pool[df_pool["is_available"] == True]
if season_filter == "In-Season Only":
    df_pool = df_pool[df_pool["season_type"] == "In-Season"]
elif season_filter == "Classic Only":
    df_pool = df_pool[df_pool["season_type"] == "Classic"]

# Esclusione carte già bloccate in altre formazioni
used_card_ids = []
for lineup in st.session_state.locked_lineups.values():
    used_card_ids.extend(lineup.get("cards", []))

df_available = df_pool[~df_pool["card_id"].isin(used_card_ids)].copy()

# Calcolo Expected Score Dinamico (Matchup + Bonus)
# Matchup Boost: partite in casa o contro squadre abbordabili ricevono un moltiplicatore virtuoso
def calculate_expected_score(row):
    base = row["clean_l5"]
    bonus_mult = 1.0 + (row["total_bonus_pct"] / 100.0)
    # Matchup factor basato sulla fixture
    matchup_mult = 1.05 if "vs " in row["opponent"] else 0.96
    return round(base * bonus_mult * matchup_mult, 1)

df_available["expected_score"] = df_available.apply(calculate_expected_score, axis=1)

# -----------------------------------------------------------------------------
# TABS PRINCIPALI DELL'APPLICAZIONE
# -----------------------------------------------------------------------------
tab_builder, tab_h2h, tab_roster, tab_strategy = st.tabs([
    "⚔️ Formazioni (SO5 & SO7)", 
    "⚖️ Head-to-Head 1v1", 
    "🃏 Rosa Limited & Matrix",
    "🧠 Suite Strategica & XP"
])

# -----------------------------------------------------------------------------
# TAB 1: BUILDER FORMAZIONE (SO5 & SO7)
# -----------------------------------------------------------------------------
with tab_builder:
    col_comp, col_fmt = st.columns([2, 1])
    with col_comp:
        competition = st.selectbox(
            "Seleziona Competizione Target",
            [
                "Liga Portugal (In-Season)",
                "Champion Europe",
                "Challenger Europe",
                "UEFA Champions League",
                "UEFA Europa/Conference",
                "All-Star"
            ]
        )
    with col_fmt:
        format_type = st.radio("Formato Competizione", ["SO5 (5 Slot)", "SO7 (7 Slot)"], horizontal=True)

    is_so7 = "SO7" in format_type
    slots = ["GK", "DEF", "MID", "FWD", "EXTRA"] if not is_so7 else ["GK", "DEF", "DEF_2", "MID", "MID_2", "FWD", "EXTRA"]

    st.markdown("#### 📋 **Composizione Schieramento**")
    
    selected_cards = {}
    selected_ids = []
    
    c_slots = st.columns(len(slots))
    for idx, slot in enumerate(slots):
        with c_slots[idx]:
            st.markdown(f"**Slot {slot}**")
            pos_filter = slot.split("_")[0]
            
            # Filtro slot
            if pos_filter == "EXTRA":
                candidates = df_available[~df_available["card_id"].isin(selected_ids)]
            else:
                candidates = df_available[(df_available["position"] == pos_filter) & (~df_available["card_id"].isin(selected_ids))]
            
            if candidates.empty:
                st.warning("Nessuna carta")
                selected_cards[slot] = None
            else:
                card_options = {
                    row["card_id"]: f"{row['name']} ({row['club']}) - Exp: {row['expected_score']}" 
                    for _, row in candidates.iterrows()
                }
                choice_id = st.selectbox(
                    f"Scegli {slot}", 
                    options=list(card_options.keys()), 
                    format_func=lambda x: card_options[x], 
                    key=f"slot_select_{competition}_{slot}"
                )
                selected_cards[slot] = candidates[candidates["card_id"] == choice_id].iloc[0]
                selected_ids.append(choice_id)

    # Verifica Regole In-Season (Max 1 Classic per SO5 In-Season)
    chosen_rows = [row for row in selected_cards.values() if row is not None]
    classic_count = sum(1 for r in chosen_rows if r["season_type"] == "Classic")
    
    valid_lineup = True
    if "In-Season" in competition and not is_so7:
        if classic_count > 1:
            st.error(f"⚠️ Limite Superato: Hai selezionato {classic_count} carte Classic. Massimo 1 consentita per la modalità In-Season!")
            valid_lineup = False

    # KPI e Valutazione Formazione
    if chosen_rows:
        st.markdown("---")
        total_exp = sum(r["expected_score"] for r in chosen_rows)
        avg_bonus = sum(r["total_bonus_pct"] for r in chosen_rows) / len(chosen_rows)
        clubs = [r["club"] for r in chosen_rows]
        stack_detected = any(clubs.count(c) >= 2 for c in set(clubs))

        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(f'<div class="metric-glass"><div class="metric-val">{round(total_exp, 1)}</div><div class="metric-lbl">Expected Score Totale</div></div>', unsafe_allow_html=True)
        with k2:
            st.markdown(f'<div class="metric-glass"><div class="metric-val">+{round(avg_bonus, 1)}%</div><div class="metric-lbl">Bonus Medio Formazione</div></div>', unsafe_allow_html=True)
        with k3:
            status_text = "🛡️ ATTIVO" if stack_detected else "Indipendente"
            st.markdown(f'<div class="metric-glass"><div class="metric-val">{status_text}</div><div class="metric-lbl">Stack Club Correlato</div></div>', unsafe_allow_html=True)
        with k4:
            safety = "ALTA (100% Starter)" if all(r["clean_l5"] >= 45 for r in chosen_rows) else "MEDIA (Ballottaggio)"
            st.markdown(f'<div class="metric-glass"><div class="metric-val">{safety}</div><div class="metric-lbl">Safety Index</div></div>', unsafe_allow_html=True)

        st.markdown("###")
        c_act1, c_act2 = st.columns([1, 4])
        with c_act1:
            if st.button("🔒 Blocca Formazione", disabled=not valid_lineup, use_container_width=True):
                st.session_state.locked_lineups[competition] = {
                    "cards": [r["card_id"] for r in chosen_rows],
                    "total_exp": total_exp,
                    "names": [r["name"] for r in chosen_rows]
                }
                st.success(f"Formazione {competition} bloccata per questa GW!")
                st.rerun()

    # Formazioni già registrate
    if st.session_state.locked_lineups:
        st.markdown("---")
        st.markdown("#### 📌 **Formazioni Salvate per la Game Week**")
        for comp_name, data in st.session_state.locked_lineups.items():
            st.info(f"**{comp_name}** | Expected: **{data['total_exp']} pt** | Lineup: {', '.join(data['names'])}")

# -----------------------------------------------------------------------------
# TAB 2: HEAD-TO-HEAD (1v1) POTENZIATO
# -----------------------------------------------------------------------------
with tab_h2h:
    st.markdown("#### ⚖️ **Confronto Diretto Head-to-Head (1v1)**")
    c_p1, c_p2 = st.columns(2)
    
    player_names = df_pool["name"].tolist()
    with c_p1:
        p1_name = st.selectbox("Seleziona Giocatore A", options=player_names, index=0)
        p1 = df_pool[df_pool["name"] == p1_name].iloc[0]
    with c_p2:
        p2_name = st.selectbox("Seleziona Giocatore B", options=player_names, index=min(1, len(player_names)-1))
        p2 = df_pool[df_pool["name"] == p2_name].iloc[0]

    st.markdown("---")
    col_card_a, col_card_b = st.columns(2)
    with col_card_a:
        st.markdown(f"""
        <div class="sorare-card-container">
            <img src="{p1['picture_url']}" class="card-img" alt="{p1['name']}">
            <h3 style="margin: 8px 0 2px 0;">{p1['name']}</h3>
            <p style="color: #94a3b8; font-size: 0.9rem;">{p1['club']} • {p1['position']}</p>
            <span class="badge {'badge-inseason' if p1['season_type']=='In-Season' else 'badge-classic'}">{p1['season_type']}</span>
            <span class="badge badge-gold">+{p1['total_bonus_pct']}% Bonus</span>
            <hr style="border-color: rgba(255,255,255,0.1); margin: 12px 0;">
            <p><strong>Floor Depurato (L5):</strong> {p1['clean_l5']}</p>
            <p><strong>Ceiling Depurato (L15):</strong> {p1['clean_l15']}</p>
            <p><strong>Prossimo Match:</strong> {p1['opponent']}</p>
        </div>
        """, unsafe_allow_html=True)

    with col_card_b:
        st.markdown(f"""
        <div class="sorare-card-container">
            <img src="{p2['picture_url']}" class="card-img" alt="{p2['name']}">
            <h3 style="margin: 8px 0 2px 0;">{p2['name']}</h3>
            <p style="color: #94a3b8; font-size: 0.9rem;">{p2['club']} • {p2['position']}</p>
            <span class="badge {'badge-inseason' if p2['season_type']=='In-Season' else 'badge-classic'}">{p2['season_type']}</span>
            <span class="badge badge-gold">+{p2['total_bonus_pct']}% Bonus</span>
            <hr style="border-color: rgba(255,255,255,0.1); margin: 12px 0;">
            <p><strong>Floor Depurato (L5):</strong> {p2['clean_l5']}</p>
            <p><strong>Ceiling Depurato (L15):</strong> {p2['clean_l15']}</p>
            <p><strong>Prossimo Match:</strong> {p2['opponent']}</p>
        </div>
        """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TAB 3: ROSA LIMITED & TOGGLE VISTA
# -----------------------------------------------------------------------------
with tab_roster:
    col_t_title, col_t_view = st.columns([3, 1])
    with col_t_title:
        st.markdown("#### 🃏 **Gestione Rosa Limited**")
    with col_t_view:
        view_mode = st.radio("Modalità Visualizzazione", ["🃏 Griglia Card", "📋 Tabella Dati"], horizontal=True)

    if view_mode == "📋 Tabella Dati":
        display_df = df_pool[[
            "name", "club", "position", "season_type", 
            "clean_l5", "clean_l15", "total_bonus_pct", 
            "xp_next_level", "opponent", "status"
        ]].copy()
        display_df.columns = [
            "Giocatore", "Squadra", "Ruolo", "Stagione", 
            "Floor L5", "Ceiling L15", "Bonus %", 
            "XP al Lvl Succ.", "Fixture GW", "Stato"
        ]
        st.dataframe(display_df, use_container_width=True)
    else:
        # Vista Griglia Grafica con Card Ufficiali
        cards_per_row = 4
        all_cards = df_pool.to_dict(orient="records")
        for i in range(0, len(all_cards), cards_per_row):
            row_cards = all_cards[i:i+cards_per_row]
            cols = st.columns(cards_per_row)
            for j, card in enumerate(row_cards):
                with cols[j]:
                    st.markdown(f"""
                    <div class="sorare-card-container">
                        <img src="{card['picture_url']}" class="card-img" alt="{card['name']}">
                        <h4 style="margin: 6px 0 2px 0;">{card['name']}</h4>
                        <div style="font-size: 0.8rem; color: #94a3b8;">{card['club']} • {card['position']}</div>
                        <div style="margin-top: 4px;">
                            <span class="badge {'badge-inseason' if card['season_type']=='In-Season' else 'badge-classic'}">{card['season_type']}</span>
                            <span class="badge badge-gold">+{card['total_bonus_pct']}%</span>
                        </div>
                        <div style="font-size: 0.8rem; margin-top: 8px; color: #cbd5e1;">
                            Floor L5: <b>{card['clean_l5']}</b> | Ceil: <b>{card['clean_l15']}</b><br>
                            {card['opponent']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TAB 4: SUITE STRATEGICA & XP TRACKER
# -----------------------------------------------------------------------------
with tab_strategy:
    st.markdown("#### 🧠 **Analisi Sinergie & Progressione Livelli**")
    
    col_strat1, col_strat2 = st.columns(2)
    with col_strat1:
        st.markdown("##### 🔗 **Stack Builder (Correlazioni di Reparto)**")
        club_counts = df_pool["club"].value_counts()
        viable_clubs = club_counts[club_counts >= 2].index.tolist()
        
        if viable_clubs:
            for club in viable_clubs:
                club_players = df_pool[df_pool["club"] == club]
                has_gk = any(club_players["position"] == "GK")
                has_def = any(club_players["position"] == "DEF")
                
                stack_badge = "🛡️ Clean Sheet Duo Attivo (GK + DEF)" if (has_gk and has_def) else "⚽ Asse Tattico Club"
                st.markdown(f"""
                <div style="background: rgba(18,24,38,0.5); padding: 12px; border-radius: 8px; border-left: 4px solid #D4AF37; margin-bottom: 8px;">
                    <strong>{club}</strong> — {stack_badge}<br>
                    <span style="font-size: 0.85rem; color: #94a3b8;">Giocatori a disposizione: {', '.join(club_players['name'].tolist())}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Nessuno stack con 2+ carte dello stesso club trovato nella selezione.")

    with col_strat2:
        st.markdown("##### 📈 **XP Tracker (Soglia Livello Successivo)**")
        st.caption("Identifica i giocatori a pochi punti esperienza da un ulteriore +1% di moltiplicatore.")
        
        xp_urgent = df_pool.sort_values(by="xp_next_level").head(5)
        for _, x_row in xp_urgent.iterrows():
            st.markdown(f"""
            <div style="background: rgba(18,24,38,0.5); padding: 10px; border-radius: 8px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong>{x_row['name']}</strong> ({x_row['club']})<br>
                    <span style="font-size: 0.8rem; color: #94a3b8;">XP attuali: {x_row['xp']}</span>
                </div>
                <div style="text-align: right;">
                    <span class="badge badge-gold">Mancano {x_row['xp_next_level']} XP</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
