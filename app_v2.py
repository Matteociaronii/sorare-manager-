import streamlit as st
import pandas as pd
import requests

# -----------------------------------------------------------------------------
# CONFIGURAZIONE PAGINA & BRANDING XT_MATTY
# -----------------------------------------------------------------------------
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
# GRAPHQL API SORARE CON PAGINAZIONE COMPLETA (TUTTE LE CARTE)
# -----------------------------------------------------------------------------
SORARE_GRAPHQL_URL = "https://api.sorare.com/graphql"
DEFAULT_SLUG = "xt_matty-0d7de6d1-d3e9-42c5-b62a-6cd4dbd8d691"

@st.cache_data(ttl=300)
def fetch_all_user_limited_cards(user_slug, jwt_token=""):
    """
    Scarica l'intera galleria di carte Limited usando la paginazione cursore (after/endCursor).
    """
    headers = {"Content-Type": "application/json"}
    if jwt_token and jwt_token.strip():
        headers["Authorization"] = f"Bearer {jwt_token.strip()}"

    query = """
    query GetUserCardsPaginated($slug: String!, $cursor: String) {
      user(slug: $slug) {
        cards(rarities: [limited], first: 50, after: $cursor) {
          pageInfo {
            hasNextPage
            endCursor
          }
          nodes {
            id
            slug
            name
            pictureUrl
            rarity
            season {
              startYear
            }
            player {
              displayName
              position
              pictureUrl
              activeClub {
                name
              }
              lastFiveSo5Appearances
              lastFifteenSo5AverageScore
            }
            xp
            bonus
            collectionBonus
          }
        }
      }
    }
    """
    
    all_nodes = []
    cursor = None
    has_next = True
    
    while has_next:
        try:
            resp = requests.post(
                SORARE_GRAPHQL_URL,
                json={"query": query, "variables": {"slug": user_slug.strip(), "cursor": cursor}},
                headers=headers,
                timeout=15
            )
            if resp.status_code == 200:
                res_json = resp.json()
                if "data" in res_json and res_json["data"] and res_json["data"].get("user"):
                    cards_data = res_json["data"]["user"]["cards"]
                    nodes = cards_data.get("nodes", [])
                    all_nodes.extend(nodes)
                    
                    page_info = cards_data.get("pageInfo", {})
                    has_next = page_info.get("hasNextPage", False)
                    cursor = page_info.get("endCursor")
                else:
                    break
            else:
                st.error(f"Errore API Sorare: codice {resp.status_code}")
                break
        except Exception as e:
            st.error(f"Errore di connessione: {str(e)}")
            break
            
    return parse_nodes(all_nodes)

def parse_nodes(nodes):
    parsed = []
    current_season_start = 2026
    
    for c in nodes:
        player = c.get("player") or {}
        active_club = (player.get("activeClub") or {}).get("name", "N/A")
        position = (player.get("position") or "EXTRA").upper()
        
        start_year = (c.get("season") or {}).get("startYear", 2024)
        is_in_season = (start_year >= current_season_start)
        season_type = "In-Season" if is_in_season else "Classic"
        
        img_url = c.get("pictureUrl") or player.get("pictureUrl") or ""
        
        raw_bonus = float(c.get("bonus") or 0.0)
        coll_bonus = float(c.get("collectionBonus") or 0.0)
        total_bonus = round(raw_bonus + coll_bonus, 1)
        
        xp = int(c.get("xp") or 0)
        xp_next = 250 - (xp % 250)
        
        clean_l5 = round(float(player.get("lastFiveSo5Appearances") or 40.0), 1)
        clean_l15 = round(float(player.get("lastFifteenSo5AverageScore") or 45.0), 1)
        
        parsed.append({
            "card_id": c.get("id"),
            "name": player.get("displayName") or c.get("name"),
            "club": active_club,
            "position": position,
            "season_type": season_type,
            "picture_url": img_url,
            "clean_l5": clean_l5,
            "clean_l15": clean_l15,
            "xp": xp,
            "xp_next_level": xp_next,
            "total_bonus_pct": total_bonus,
            "collection_bonus": round(coll_bonus, 1),
            "status": "ACTIVE",
            "is_available": True,
            "has_fixture": True,
            "opponent": "Partita GW"
        })
    return pd.DataFrame(parsed)

# -----------------------------------------------------------------------------
# SESSION STATE & RESET
# -----------------------------------------------------------------------------
if "locked_lineups" not in st.session_state:
    st.session_state.locked_lineups = {}

# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚡ **XT_Matty Command**")
    user_slug = st.text_input("Sorare Manager Slug", value=DEFAULT_SLUG)
    jwt_input = st.text_input("Sorare JWT Token (Opzionale)", type="password")
    
    col_sync1, col_sync2 = st.columns(2)
    with col_sync1:
        if st.button("🔄 Sync Club", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
                
    with col_sync2:
        if st.button("🗑️ Reset GW", use_container_width=True):
            st.session_state.locked_lineups = {}
            st.rerun()

    st.markdown("---")
    st.markdown("#### 🎯 **Filtri Rosa**")
    season_filter = st.selectbox("Filtro Stagione", ["Tutte", "In-Season Only", "Classic Only"])

# -----------------------------------------------------------------------------
# HEADER
# -----------------------------------------------------------------------------
st.markdown("""
<div class="brand-header">
    <h1 class="brand-title">XT_MATTY • SORARE PRO HUB</h1>
    <div class="brand-subtitle">Manager Suite Ufficiale • Sync Club Completo • Card Matrix Reale</div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# CARICAMENTO TOTALE DELLA ROSA
# -----------------------------------------------------------------------------
with st.spinner("Sincronizzazione di tutte le carte Limited del tuo Club..."):
    df_raw = fetch_all_user_limited_cards(user_slug, jwt_input)

if df_raw.empty:
    st.warning("⚠️ Nessuna carta Limited trovata per questo account o connessione in corso...")
    st.stop()

df_pool = df_raw.copy()

if season_filter == "In-Season Only":
    df_pool = df_pool[df_pool["season_type"] == "In-Season"]
elif season_filter == "Classic Only":
    df_pool = df_pool[df_pool["season_type"] == "Classic"]

# Esclusione carte bloccate
used_card_ids = []
for lineup in st.session_state.locked_lineups.values():
    used_card_ids.extend(lineup.get("cards", []))

df_available = df_pool[~df_pool["card_id"].isin(used_card_ids)].copy()

def calculate_expected_score(row):
    base = row["clean_l5"]
    bonus_mult = 1.0 + (row["total_bonus_pct"] / 100.0)
    return round(base * bonus_mult, 1)

df_available["expected_score"] = df_available.apply(calculate_expected_score, axis=1)

# -----------------------------------------------------------------------------
# TABS PRINCIPALI
# -----------------------------------------------------------------------------
tab_builder, tab_h2h, tab_roster, tab_strategy = st.tabs([
    "⚔️ Formazioni (SO5 & SO7)", 
    "⚖️ Head-to-Head 1v1", 
    f"🃏 Rosa Limited ({len(df_pool)} Carte)",
    "🧠 Suite Strategica & XP"
])

# -----------------------------------------------------------------------------
# TAB 1: BUILDER FORMAZIONE
# -----------------------------------------------------------------------------
with tab_builder:
    col_comp, col_fmt = st.columns([2, 1])
    with col_comp:
        competition = st.selectbox(
            "Seleziona Competizione Target",
            [
                "Champion Europe (Classic SO7)",
                "Challenger Europe",
                "Liga Portugal (In-Season)",
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
            
            if pos_filter == "EXTRA":
                candidates = df_available[~df_available["card_id"].isin(selected_ids)]
            else:
                candidates = df_available[(df_available["position"] == pos_filter) & (~df_available["card_id"].isin(selected_ids))]
            
            if candidates.empty:
                st.warning("Nessuna")
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
                    key=f"slot_sel_{competition}_{slot}"
                )
                selected_cards[slot] = candidates[candidates["card_id"] == choice_id].iloc[0]
                selected_ids.append(choice_id)

    chosen_rows = [row for row in selected_cards.values() if row is not None]
    classic_count = sum(1 for r in chosen_rows if r["season_type"] == "Classic")
    
    valid_lineup = True
    if "In-Season" in competition and not is_so7:
        if classic_count > 1:
            st.error(f"⚠️ Limite Superato: Hai selezionato {classic_count} carte Classic. Massimo 1 consentita per In-Season!")
            valid_lineup = False

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
            safety = "ALTA" if all(r["clean_l5"] >= 45 for r in chosen_rows) else "MEDIA"
            st.markdown(f'<div class="metric-glass"><div class="metric-val">{safety}</div><div class="metric-lbl">Safety Index</div></div>', unsafe_allow_html=True)

        st.markdown("###")
        if st.button("🔒 Salva & Blocca Formazione", disabled=not valid_lineup):
            st.session_state.locked_lineups[competition] = {
                "cards": [r["card_id"] for r in chosen_rows],
                "total_exp": total_exp,
                "names": [r["name"] for r in chosen_rows]
            }
            st.success(f"Formazione salvata con successo per {competition}!")
            st.rerun()

    if st.session_state.locked_lineups:
        st.markdown("---")
        st.markdown("#### 📌 **Formazioni Salvate per la Game Week**")
        for comp_name, data in st.session_state.locked_lineups.items():
            st.info(f"**{comp_name}** | Punti Attesi: **{data['total_exp']} pt** | Rosa: {', '.join(data['names'])}")

# -----------------------------------------------------------------------------
# TAB 2: HEAD-TO-HEAD (1v1)
# -----------------------------------------------------------------------------
with tab_h2h:
    st.markdown("#### ⚖️ **Confronto Diretto Head-to-Head (1v1)**")
    player_names = df_pool["name"].tolist()
    
    c_p1, c_p2 = st.columns(2)
    with c_p1:
        p1_name = st.selectbox("Seleziona Giocatore A", options=player_names, index=0)
        p1 = df_pool[df_pool["name"] == p1_name].iloc[0]
    with c_p2:
        p2_name = st.selectbox("Seleziona Giocatore B", options=player_names, index=min(1, len(player_names)-1))
        p2 = df_pool[df_pool["name"] == p2_name].iloc[0]

    st.markdown("---")
    col_card_a, col_card_b = st.columns(2)
    
    with col_card_a:
        img_a = f'<img src="{p1["picture_url"]}" class="card-img">' if p1["picture_url"] else ''
        st.markdown(f"""
        <div class="sorare-card-container">
            {img_a}
            <h3 style="margin: 8px 0 2px 0;">{p1['name']}</h3>
            <p style="color: #94a3b8; font-size: 0.9rem;">{p1['club']} • {p1['position']}</p>
            <span class="badge {'badge-inseason' if p1['season_type']=='In-Season' else 'badge-classic'}">{p1['season_type']}</span>
            <span class="badge badge-gold">+{p1['total_bonus_pct']}% Bonus</span>
            <hr style="border-color: rgba(255,255,255,0.1); margin: 12px 0;">
            <p><strong>L5:</strong> {p1['clean_l5']} | <strong>L15:</strong> {p1['clean_l15']}</p>
            <p><strong>Esperienza XP:</strong> {p1['xp']} (Mancano {p1['xp_next_level']} al lvl succ.)</p>
        </div>
        """, unsafe_allow_html=True)

    with col_card_b:
        img_b = f'<img src="{p2["picture_url"]}" class="card-img">' if p2["picture_url"] else ''
        st.markdown(f"""
        <div class="sorare-card-container">
            {img_b}
            <h3 style="margin: 8px 0 2px 0;">{p2['name']}</h3>
            <p style="color: #94a3b8; font-size: 0.9rem;">{p2['club']} • {p2['position']}</p>
            <span class="badge {'badge-inseason' if p2['season_type']=='In-Season' else 'badge-classic'}">{p2['season_type']}</span>
            <span class="badge badge-gold">+{p2['total_bonus_pct']}% Bonus</span>
            <hr style="border-color: rgba(255,255,255,0.1); margin: 12px 0;">
            <p><strong>L5:</strong> {p2['clean_l5']} | <strong>L15:</strong> {p2['clean_l15']}</p>
            <p><strong>Esperienza XP:</strong> {p2['xp']} (Mancano {p2['xp_next_level']} al lvl succ.)</p>
        </div>
        """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TAB 3: ROSA LIMITED & MATRIX
# -----------------------------------------------------------------------------
with tab_roster:
    col_t_title, col_t_view = st.columns([3, 1])
    with col_t_title:
        st.markdown(f"#### 🃏 **Tutte le Carte Limited del Club ({len(df_pool)})**")
    with col_t_view:
        view_mode = st.radio("Visualizzazione", ["🃏 Griglia Card", "📋 Tabella Dati"], horizontal=True)

    if view_mode == "📋 Tabella Dati":
        disp_df = df_pool[[
            "name", "club", "position", "season_type", 
            "clean_l5", "clean_l15", "total_bonus_pct", 
            "xp_next_level"
        ]].copy()
        disp_df.columns = [
            "Giocatore", "Club", "Ruolo", "Stagione", 
            "Media L5", "Media L15", "Bonus %", "XP al Lvl Succ."
        ]
        st.dataframe(disp_df, use_container_width=True)
    else:
        cards_per_row = 4
        all_cards = df_pool.to_dict(orient="records")
        for i in range(0, len(all_cards), cards_per_row):
            row_cards = all_cards[i:i+cards_per_row]
            cols = st.columns(cards_per_row)
            for j, card in enumerate(row_cards):
                with cols[j]:
                    img_elem = f'<img src="{card["picture_url"]}" class="card-img" alt="{card["name"]}">' if card["picture_url"] else ''
                    st.markdown(f"""
                    <div class="sorare-card-container">
                        {img_elem}
                        <h4 style="margin: 6px 0 2px 0;">{card['name']}</h4>
                        <div style="font-size: 0.8rem; color: #94a3b8;">{card['club']} • {card['position']}</div>
                        <div style="margin-top: 4px;">
                            <span class="badge {'badge-inseason' if card['season_type']=='In-Season' else 'badge-classic'}">{card['season_type']}</span>
                            <span class="badge badge-gold">+{card['total_bonus_pct']}%</span>
                        </div>
                        <div style="font-size: 0.8rem; margin-top: 8px; color: #cbd5e1;">
                            L5: <b>{card['clean_l5']}</b> | L15: <b>{card['clean_l15']}</b>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TAB 4: SUITE STRATEGICA & XP TRACKER
# -----------------------------------------------------------------------------
with tab_strategy:
    st.markdown("#### 🧠 **Sinergie Club & Progressione XP**")
    
    col_strat1, col_strat2 = st.columns(2)
    with col_strat1:
        st.markdown("##### 🔗 **Stack Builder (Accoppiate di Squadra)**")
        club_counts = df_pool["club"].value_counts()
        viable_clubs = club_counts[club_counts >= 2].index.tolist()
        
        if viable_clubs:
            for club in viable_clubs:
                club_players = df_pool[df_pool["club"] == club]
                has_gk = any(club_players["position"] == "GK")
                has_def = any(club_players["position"] == "DEF")
                
                stack_badge = "🛡️ Clean Sheet Stack (GK + DEF)" if (has_gk and has_def) else "⚽ Asse Tattico Club"
                st.markdown(f"""
                <div style="background: rgba(18,24,38,0.5); padding: 12px; border-radius: 8px; border-left: 4px solid #D4AF37; margin-bottom: 8px;">
                    <strong>{club}</strong> — {stack_badge}<br>
                    <span style="font-size: 0.85rem; color: #94a3b8;">Giocatori nel tuo club: {', '.join(club_players['name'].tolist())}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Nessuno stack con 2+ carte dello stesso club trovato.")

    with col_strat2:
        st.markdown("##### 📈 **XP Tracker (Soglia Livello Successivo)**")
        st.caption("Carte più vicine allo scatto di livello (+1% bonus permanente).")
        
        xp_urgent = df_pool.sort_values(by="xp_next_level").head(6)
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
