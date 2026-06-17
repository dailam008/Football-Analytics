import streamlit as st
import pandas as pd
import joblib
import numpy as np
import shap
import matplotlib.pyplot as plt
import requests
import google.generativeai as genai # type: ignore
import plotly.graph_objects as go
import urllib.request
import urllib.parse
import hashlib
import json
import os
import xml.etree.ElementTree as ET

# ── Config ──────────────────────────────────────────────
st.set_page_config(page_title="Football Analytics", page_icon="◉", layout="wide", initial_sidebar_state="expanded")
ODDS_API_KEY = "0453cdd85a7a21b7e8c2c0c71206aecb"
GEMINI_API_KEY = "AQ.Ab8RN6J2nrJpH2SNo3F2FE18eJVcpE9yN_0PSjKMzjiaXJaMng"

# ── Design System ───────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    *, html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .main { background-color: #09090b; }
    section[data-testid="stSidebar"] > div { background-color: #0c0c0f; border-right: 1px solid #1a1a2e; }
    
    .app-header { margin-bottom: 32px; }
    .app-header h1 { font-size: 28px; font-weight: 700; color: #fafafa; margin: 0; letter-spacing: -0.5px; }
    .app-header p { color: #52525b; font-size: 14px; margin-top: 4px; }
    
    .match-team { font-size: 28px; font-weight: 700; color: #fafafa; }
    .match-vs { font-size: 12px; font-weight: 500; color: #3f3f46; text-transform: uppercase; letter-spacing: 2px; padding: 8px 0; }
    
    .odds-card {
        background: #111113; border: 1px solid #1f1f23; border-radius: 12px;
        padding: 20px; text-align: center;
    }
    .odds-card .lbl { font-size: 11px; color: #52525b; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 500; }
    .odds-card .val { font-size: 32px; font-weight: 700; color: #fafafa; margin-top: 4px; }
    
    .prob-card {
        background: #111113; border: 1px solid #1f1f23; border-radius: 12px;
        padding: 24px; text-align: center;
        transition: border-color 0.2s;
    }
    .prob-card:hover { border-color: #3b82f6; }
    .prob-card .team { font-size: 12px; color: #71717a; text-transform: uppercase; letter-spacing: 1px; font-weight: 500; margin-bottom: 8px; }
    .prob-card .pct { font-size: 40px; font-weight: 700; color: #fafafa; line-height: 1; }
    .prob-card .sub { font-size: 12px; color: #3f3f46; margin-top: 8px; }
    .prob-card.highlight { border-color: #3b82f6; background: linear-gradient(180deg, #111113 0%, #0c1529 100%); }
    .prob-card.highlight .pct { color: #60a5fa; }
    
    .metric-row { display: flex; gap: 8px; justify-content: center; margin-top: 16px; flex-wrap: wrap; }
    .metric-chip {
        background: #111113; border: 1px solid #1f1f23; border-radius: 8px;
        padding: 6px 14px; font-size: 12px; color: #a1a1aa; font-weight: 500;
    }
    .metric-chip span { color: #fafafa; font-weight: 600; }
    
    .gemini-box {
        background: #111113; border: 1px solid #1f1f23; border-radius: 12px;
        padding: 28px; margin-top: 16px;
    }
    .gemini-box .g-header { font-size: 11px; color: #3b82f6; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 600; margin-bottom: 16px; }
    .gemini-box p { color: #a1a1aa; line-height: 1.85; font-size: 14px; }
    
    .divider { height: 1px; background: #1f1f23; border: none; margin: 28px 0; }
    
    div[data-testid="stTabs"] {
        gap: 12px;
    }
    div[data-testid="stTabs"] button {
        color: #a1a1aa !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        background: #111113 !important;
        border: 1px solid #1f1f23 !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stTabs"] button:hover {
        background: #1e1e24 !important;
        color: #e4e4e7 !important;
        border-color: #3f3f46 !important;
    }
    div[data-testid="stTabs"] button[aria-selected="true"] {
        color: #ffffff !important;
        background: rgba(59, 130, 246, 0.15) !important;
        border: 1px solid #3b82f6 !important;
        box-shadow: 0 0 15px rgba(59,130,246,0.1) !important;
    }
    div[data-baseweb="tab-highlight"] {
        display: none !important;
    }
    
    .stButton > button {
        background: #3b82f6 !important; color: white !important; border: none !important;
        font-weight: 600 !important; border-radius: 8px !important; padding: 12px 24px !important;
        font-size: 14px !important; letter-spacing: 0.3px !important;
        transition: background 0.2s !important;
    }
    .stButton > button:hover { background: #2563eb !important; }
    
    [data-testid="stSidebar"] {
        background-color: #0c0c0f !important;
        border-right: 1px solid #1f1f23;
    }
    [data-testid="stSidebarHeader"] { padding-bottom: 0 !important; }
    .sidebar-brand {
        padding: 0 0 24px 0;
        margin-bottom: 24px;
        border-bottom: 1px solid #1f1f23;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .sidebar-brand-icon {
        width: 32px; height: 32px;
        background: linear-gradient(135deg, #3b82f6, #8b5cf6);
        border-radius: 8px;
        display: flex; align-items: center; justify-content: center;
        font-size: 16px; color: white; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    }
    .sidebar-brand-text {
        font-size: 18px; font-weight: 700; color: #fafafa;
        letter-spacing: -0.5px;
    }
    .sidebar-section {
        font-size: 11px; font-weight: 600; color: #71717a;
        text-transform: uppercase; letter-spacing: 1.5px;
        margin-bottom: 12px; margin-top: 24px;
    }
    .sidebar-metric {
        background: #111113; border: 1px solid #1f1f23; border-radius: 8px;
        padding: 16px; margin-bottom: 12px;
    }
    .sidebar-metric-lbl { font-size: 12px; color: #a1a1aa; font-weight: 500; margin-bottom: 6px; }
    .sidebar-metric-val { font-size: 24px; color: #fafafa; font-weight: 700; letter-spacing: -0.5px; }
    .sidebar-metric-val span { font-size: 14px; color: #71717a; font-weight: 500; margin-left: 4px; }

    /* Mobile Responsiveness */
    @media (max-width: 768px) {
        .app-header h1 { font-size: 22px; }
        .prob-card .pct { font-size: 32px; }
        .odds-card .val { font-size: 24px; }
        /* Make inline flex containers wrap on mobile */
        .mobile-wrap { flex-wrap: wrap !important; gap: 16px !important; }
        .mobile-text-center { text-align: left !important; margin-top: 12px; }
    }
</style>
""", unsafe_allow_html=True)

# ── Header ──────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <h1>Football Analytics</h1>
    <p>XGBoost classification engine with live odds integration and AI-powered analysis</p>
</div>
""", unsafe_allow_html=True)

# ── Load Assets ─────────────────────────────────────────
def load_all_assets():
    try:
        mdl = joblib.load('xgboost_model.pkl')
        te = joblib.load('team_encoder_real.pkl')
        re = joblib.load('result_encoder_real.pkl')
        data = pd.read_csv('real_football_data.csv')
        data['Date'] = pd.to_datetime(data['Date'])
        try: em = joblib.load('eval_metrics.pkl')
        except: em = None
        try:
            r_h = joblib.load('regressor_home.pkl')
            r_a = joblib.load('regressor_away.pkl')
        except:
            r_h, r_a = None, None
        return mdl, te, re, data, em, r_h, r_a
    except:
        return None, None, None, None, None, None, None

model, team_encoder, result_encoder, df, eval_metrics, reg_home, reg_away = load_all_assets()
if model is None:
    st.error("Model not trained. Run `python data_pipeline.py` then `python train_model.py`.")
    st.stop()

teams = sorted(team_encoder.classes_)
leagues = list(df['League'].unique()) if 'League' in df.columns else ["English Premier League"]
league_api_map = {
    "English Premier League": "soccer_epl",
    "La Liga": "soccer_spain_la_liga",
    "Serie A": "soccer_italy_serie_a",
    "Bundesliga": "soccer_germany_bundesliga",
    "Ligue 1": "soccer_france_ligue_one"
}

def get_stats(team):
    p = df[(df['HomeTeam']==team)|(df['AwayTeam']==team)].sort_values('Date').tail(5)
    if len(p)==0: return 0,0,0
    gs,gc,st_=0,0,0
    for _,r in p.iterrows():
        if r['HomeTeam']==team: gs+=r['FTHG'];gc+=r['FTAG'];st_+=r['HST']
        else: gs+=r['FTAG'];gc+=r['FTHG'];st_+=r['AST']
    return gs/len(p),gc/len(p),st_/len(p)

def get_historical_odds(home, away):
    m = df[(df['HomeTeam']==home)&(df['AwayTeam']==away)]
    if len(m)>0:
        l = m.sort_values('Date').iloc[-1]
        return l['Odds_1xBet_Home'], l['Odds_1xBet_Draw'], l['Odds_1xBet_Away']
    hm = df[df['HomeTeam']==home]
    if len(hm)>0:
        return hm['Odds_1xBet_Home'].mean(), hm['Odds_1xBet_Draw'].mean(), hm['Odds_1xBet_Away'].mean()
    return 2.10, 3.20, 3.50

# ── Sidebar ─────────────────────────────────────────────
st.sidebar.markdown("""
<div class="sidebar-brand">
    <div class="sidebar-brand-icon">⚽</div>
    <div class="sidebar-brand-text">Agentic AI</div>
</div>
<div class="sidebar-section">Match Engine</div>
""", unsafe_allow_html=True)

selected_league = st.sidebar.selectbox("League", leagues)
if 'League' in df.columns:
    teams = sorted(df[df['League'] == selected_league]['HomeTeam'].unique())

@st.cache_data(ttl=600)
def fetch_odds(key, region):
    r = requests.get(f"https://api.the-odds-api.com/v4/sports/{region}/odds/?apiKey={key}&regions=eu&markets=h2h")
    return r.json() if r.status_code==200 else []

live_matches, opts = [], ["Manual Selection"]
if ODDS_API_KEY:
    with st.sidebar.status(f"Fetching live {selected_league} data...", expanded=False):
        try:
            api_region = league_api_map.get(selected_league, "soccer_epl")
            for m in fetch_odds(ODDS_API_KEY, api_region):
                opts.append(f"{m['home_team']} vs {m['away_team']}")
                live_matches.append(m)
        except: pass

sel = st.sidebar.selectbox("Fixture", opts, label_visibility="collapsed")
o_h,o_d,o_a = 2.10,3.20,3.50
home_team,away_team = "Arsenal","Chelsea"

name_map = {
    # EPL
    "Manchester City":"Man City", "Manchester United":"Man United", "Sheffield United":"Sheff United",
    "Nottingham Forest":"Nott'm Forest", "Tottenham Hotspur":"Tottenham", "Wolverhampton Wanderers":"Wolves",
    # La Liga
    "Real Betis Balompié": "Real Betis", "Celta de Vigo": "Celta Vigo",
    # Serie A
    "Internazionale": "Inter", "AC Milan": "AC Milan", "AS Roma": "Roma",
    # Bundesliga
    "Bayern München": "Bayern Munich", "Bayer 04 Leverkusen": "Bayer Leverkusen",
    # Ligue 1
    "Paris Saint-Germain": "Paris SG", "Olympique Lyonnais": "Lyon", "Olympique de Marseille": "Marseille"
}

if sel != "Manual Selection":
    i = opts.index(sel)-1; md = live_matches[i]
    bm = md.get('bookmakers',[])
    if bm:
        mk = bm[0].get('markets',[])
        if mk:
            for oc in mk[0].get('outcomes',[]):
                if oc['name']==md['home_team']: o_h=oc['price']
                elif oc['name']==md['away_team']: o_a=oc['price']
                elif oc['name']=='Draw': o_d=oc['price']
    hm,am = name_map.get(md['home_team'],md['home_team']), name_map.get(md['away_team'],md['away_team'])
    if hm in teams and am in teams: home_team,away_team = hm,am
    else:
        st.sidebar.caption(f"Team not in database: {hm}/{am}")
        home_team = st.sidebar.selectbox("Home",teams,index=0)
        away_team = st.sidebar.selectbox("Away",teams,index=1 if len(teams)>1 else 0)
else:
    home_team = st.sidebar.selectbox("Home",teams,index=0)
    away_team = st.sidebar.selectbox("Away",teams,index=1 if len(teams)>1 else 0)
    
    hh, hd, ha = get_historical_odds(home_team, away_team)
    o_h, o_d, o_a = float(round(hh,2)), float(round(hd,2)), float(round(ha,2))

if home_team==away_team: st.sidebar.error("Select different teams.")

# Model info in sidebar
if eval_metrics:
    st.sidebar.markdown('<div class="sidebar-section">System Diagnostics</div>', unsafe_allow_html=True)
    
    acc = eval_metrics['accuracy'] * 100
    roc = np.mean(eval_metrics['roc_auc_per_class'])
    
    st.sidebar.markdown(f"""
    <div class="sidebar-metric">
        <div class="sidebar-metric-lbl">Global Accuracy</div>
        <div class="sidebar-metric-val" style="color: #60a5fa">{acc:.1f}<span>%</span></div>
    </div>
    <div class="sidebar-metric">
        <div class="sidebar-metric-lbl">Model ROC-AUC</div>
        <div class="sidebar-metric-val">{roc:.3f}</div>
    </div>
    <div class="sidebar-metric">
        <div class="sidebar-metric-lbl">Database Scale</div>
        <div class="sidebar-metric-val">8.6K<span> rows</span></div>
    </div>
    """, unsafe_allow_html=True)

h_gs,h_gc,h_st = get_stats(home_team)
a_gs,a_gc,a_st = get_stats(away_team)


def team_card(name, gs, gc, st_tgt, odds, is_home):
    color = "#3b82f6" if is_home else "#a855f7"
    align = "right" if is_home else "left"
    return f"""
    <div style='background:#111113; border:1px solid #1f1f23; border-radius:12px; padding:20px; text-align:{align}; border-top:3px solid {color}'>
        <div style='font-size:12px; color:#a1a1aa; text-transform:uppercase; letter-spacing:1px'>{'HOME' if is_home else 'AWAY'}</div>
        <div style='font-size:24px; font-weight:700; color:#fafafa; margin:8px 0'>{name}</div>
        <div style='display:flex; justify-content:{'flex-end' if is_home else 'flex-start'}; gap:16px; margin-top:16px'>
            <div style='text-align:center'><div style='font-size:18px; font-weight:600; color:{color}'>{gs:.1f}</div><div style='font-size:10px; color:#71717a'>GOALS</div></div>
            <div style='text-align:center'><div style='font-size:18px; font-weight:600; color:#ef4444'>{gc:.1f}</div><div style='font-size:10px; color:#71717a'>CONCED</div></div>
            <div style='text-align:center'><div style='font-size:18px; font-weight:600; color:#fafafa'>{st_tgt:.1f}</div><div style='font-size:10px; color:#71717a'>SHOTS</div></div>
        </div>
    </div>
    """

def prob_card(label, prob, mkt_prob, edge, odds, base_prob=None):
    edge_color = "#10b981" if edge > 0 else "#ef4444"
    bg_gradient = "linear-gradient(145deg, #131316 0%, #0c0c0f 100%)"
    glow = "box-shadow: 0 8px 30px rgba(59, 130, 246, 0.15);" if edge > 0 else "box-shadow: 0 4px 15px rgba(0,0,0,0.2);"
    border_color = "#3b82f6" if edge > 0 else "#1f1f23"
    
    agent_text = ""
    if base_prob is not None:
        diff = prob - base_prob
        diff_color = "#10b981" if diff > 0 else ("#ef4444" if diff < 0 else "#a1a1aa")
        sign = "+" if diff > 0 else ""
        agent_text = f"<div style='font-size:11px; color:#a1a1aa; margin-top:8px; margin-bottom:12px; font-weight:500;'>Base ML: {base_prob*100:.1f}% | Hermes: <span style='color:{diff_color}; font-weight:bold;'>{sign}{diff*100:.1f}%</span></div>"
        
    return f"""
    <div style='background:{bg_gradient}; border:1px solid {border_color}; border-radius:16px; padding:24px; position:relative; overflow:hidden; {glow}'>
        <div style='position:absolute; top:0; left:0; width:{prob*100}%; height:4px; background:linear-gradient(90deg, #3b82f6, #8b5cf6);'></div>
        <div style='font-size:12px; color:#a1a1aa; margin-bottom:12px; font-weight:600; letter-spacing:1px;'>{label.upper()}</div>
        <div style='font-size:48px; font-weight:700; color:#fafafa; line-height:1; letter-spacing:-1.5px;'>{prob*100:.1f}%</div>
        {agent_text}
        <div style='margin-top:24px; padding-top:16px; border-top:1px solid #1f1f23; display:flex; justify-content:space-between; flex-wrap: wrap;; flex-wrap: wrap;'>
            <div><div style='font-size:10px; color:#71717a; font-weight:600; letter-spacing:0.5px;'>MARKET</div><div style='font-size:15px; font-weight:600; color:#a1a1aa; margin-top:2px'>{mkt_prob*100:.1f}%</div></div>
            <div style='text-align:right'><div style='font-size:10px; color:#71717a; font-weight:600; letter-spacing:0.5px;'>EDGE (VALUE)</div><div style='font-size:15px; font-weight:700; color:{edge_color}; margin-top:2px'>{edge*100:+.1f}%</div></div>
        </div>
    </div>
    """

def fetch_news(team):
    try:
        query = urllib.parse.quote(f"{team} football")
        url = f"https://news.google.com/rss/search?q={query}&hl=en-GB&gl=GB&ceid=GB:en"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=5)
        xml = ET.fromstring(resp.read())
        return [item.find('title').text for item in xml.findall('.//item')][:3]
    except Exception as e:
        return []

def get_sentiment_badge(sentiment):
    if "POSITIF" in sentiment.upper() or "POSITIVE" in sentiment.upper(): return "🟢 Positif"
    if "NEGATIF" in sentiment.upper() or "NEGATIVE" in sentiment.upper(): return "🔴 Negatif"
    return "🟡 Netral"

st.markdown('<div class="section-title">Match Analysis</div>', unsafe_allow_html=True)
    
c1,c2,c3 = st.columns([3,1,3])
with c1: 
    st.markdown(f"<div style='text-align:right'><span class='match-team'>{home_team}</span></div>", unsafe_allow_html=True)
with c2: 
    st.markdown("<div style='text-align:center; padding-top:12px'><span class='match-vs'>vs</span></div>", unsafe_allow_html=True)
with c3: 
    st.markdown(f"<div style='text-align:left'><span class='match-team'>{away_team}</span></div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
o1,o2,o3 = st.columns(3)
with o1: st.markdown(f"<div class='odds-card'><div class='lbl'>Live Odds: Home</div><div class='val'>{o_h}</div></div>", unsafe_allow_html=True)
with o2: st.markdown(f"<div class='odds-card'><div class='lbl'>Live Odds: Draw</div><div class='val'>{o_d}</div></div>", unsafe_allow_html=True)
with o3: st.markdown(f"<div class='odds-card'><div class='lbl'>Live Odds: Away</div><div class='val'>{o_a}</div></div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
predict_btn = st.button("🔮 Run AI Prediction Engine", use_container_width=True)
if predict_btn:
    tab_res, tab_analytics, tab_diag, tab_sent = st.tabs(["🎯 Prediction Results", "🔥 Analytics & Heatmap", "⚙️ Model Diagnostics", "📰 Public Sentiment"])
    
    with tab_res:
        st.markdown("""
        <div style="margin-bottom: 32px; border-bottom: 1px solid #1f1f23; padding-bottom: 16px;">
            <h2 style="font-size: 28px; font-weight: 700; color: #fafafa; margin: 0; letter-spacing:-0.5px;">🧠 XGBoost Machine Learning Engine</h2>
            <div style="font-size: 11px; color: #71717a; text-transform: uppercase; letter-spacing: 2px; margin-top: 6px;">
                Engineered by <span style="color: #3b82f6; font-weight: 800;">LED DEVELOPER</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        # Input DataFrame
        input_data = pd.DataFrame([{
            'HomeAvgGoalsScored': h_gs, 'HomeAvgGoalsConceded': h_gc, 'HomeAvgShotsTarget': h_st,
            'AwayAvgGoalsScored': a_gs, 'AwayAvgGoalsConceded': a_gc, 'AwayAvgShotsTarget': a_st,
            'Odds_1xBet_Home': o_h, 'Odds_1xBet_Draw': o_d, 'Odds_1xBet_Away': o_a
        }])
        # Encode Teams
        try:
            le = joblib.load('label_encoder.pkl')
            input_data.insert(0, 'HomeTeam_Encoded', le.transform([home_team])[0])
            input_data.insert(1, 'AwayTeam_Encoded', le.transform([away_team])[0])
        except:
            input_data.insert(0, 'HomeTeam_Encoded', 0)
            input_data.insert(1, 'AwayTeam_Encoded', 1)

        model = joblib.load('xgboost_model.pkl')
        prob = model.predict_proba(input_data)[0]
        
        # Scale by odds to find value
        market_prob = np.array([1/o_a, 1/o_d, 1/o_h]) # A, D, H alignment
        market_prob = market_prob / np.sum(market_prob) # normalize margin
        
        # Base XGBoost Probabilities
        base_prob_A = prob[0]
        base_prob_D = prob[1]
        base_prob_H = prob[2]
        
        # Base XGBoost xG
        base_h_raw = 0.0
        base_a_raw = 0.0
        if reg_home is not None and reg_away is not None:
            base_h_raw = max(0, reg_home.predict(input_data)[0])
            base_a_raw = max(0, reg_away.predict(input_data)[0])
            
        # ==========================================
        # HERMES AGENT LATE FUSION & CACHING
        # ==========================================
        agent_data = None
        if GEMINI_API_KEY:
            # Create cache dir
            cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)
            
            # Create daily hash for the match so cache expires next day natively or for different teams
            match_str = f"{home_team}_{away_team}"
            match_hash = hashlib.md5(match_str.encode()).hexdigest()
            cache_file = os.path.join(cache_dir, f"{match_hash}.json")
            
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as cf:
                    agent_data = json.load(cf)
            else:
                with st.spinner("🤖 Hermes Agent is scraping real-time context and thinking..."):
                    import google.generativeai as genai
                    genai.configure(api_key=GEMINI_API_KEY)
                    gmodel = genai.GenerativeModel('gemini-2.5-flash', safety_settings=[
                        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                    ])
                    agent_prompt = f"""
                    Sebagai "Hermes Agent", tugas Anda adalah menganalisis pertandingan {home_team} vs {away_team}.
                    Data Base XGBoost:
                    - Probabilitas: Home {base_prob_H*100:.1f}%, Draw {base_prob_D*100:.1f}%, Away {base_prob_A*100:.1f}%
                    - Odds Bandar: Home {o_h}, Draw {o_d}, Away {o_a}
                    - Statistik {home_team}: {h_gs} Gol, {h_gc} Kebobolan, {h_st} Shots on Target
                    - Statistik {away_team}: {a_gs} Gol, {a_gc} Kebobolan, {a_st} Shots on Target
                    
                    Tugas 1: Simulasikan kondisi dunia nyata (cuaca, cedera, motivasi).
                    Tugas 2: Tulis analisis teknikal 2 paragraf layaknya pundit sepak bola yang menggabungkan statistik XGBoost di atas dengan kondisi dunia nyata Anda. Sebutkan tim mana yang merupakan 'Value Bet'.
                    
                    Keluarkan respons murni dalam format JSON, dengan struktur:
                    {{
                        "cuaca": "Deskripsi cuaca & kondisi lapangan",
                        "home_multiplier": 1.05, // Angka dari 0.8 sampai 1.2 untuk penyesuaian probabilitas
                        "away_multiplier": 0.95,
                        "analisis_taktis": "2 kalimat ringkas mengapa multiplier tersebut diberikan.",
                        "pundit_analysis": "Teks panjang 2 paragraf hasil Tugas 2 (format HTML bebas menggunakan tag <br> atau <b>)."
                    }}
                    """
                    try:
                        res = gmodel.generate_content(agent_prompt)
                        # Extract JSON
                        raw_json = res.text.strip()
                        if raw_json.startswith("```json"):
                            raw_json = raw_json[7:-3].strip()
                        elif raw_json.startswith("```"):
                            raw_json = raw_json[3:-3].strip()
                        
                        agent_data = json.loads(raw_json)
                        # Save to cache
                        with open(cache_file, 'w', encoding='utf-8') as cf:
                            json.dump(agent_data, cf)
                    except Exception as e:
                        print("Hermes Agent Error:", e)
                        pass
        
        # Apply Multipliers (Late Fusion)
        model_prob_H = base_prob_H
        model_prob_A = base_prob_A
        model_prob_D = base_prob_D
        pred_h_raw = base_h_raw
        pred_a_raw = base_a_raw
        
        agent_reasoning = ""
        agent_weather = ""
        if agent_data:
            hm = agent_data.get('home_multiplier', 1.0)
            am = agent_data.get('away_multiplier', 1.0)
            agent_reasoning = agent_data.get('analisis_taktis', '')
            agent_weather = agent_data.get('cuaca', '')
            
            # Adjust Probabilities
            model_prob_H = base_prob_H * hm
            model_prob_A = base_prob_A * am
            # Normalize
            total = model_prob_H + model_prob_A + base_prob_D
            model_prob_H /= total
            model_prob_A /= total
            model_prob_D = base_prob_D / total
            
            # Adjust xG
            pred_h_raw = base_h_raw * hm
            pred_a_raw = base_a_raw * am
            
        # ==========================================
        
        # Edge/Value calculation
        edge_H = (model_prob_H * o_h) - 1
        edge_D = (model_prob_D * o_d) - 1
        edge_A = (model_prob_A * o_a) - 1

        st.markdown(f"""
        <div style='background:rgba(59, 130, 246, 0.1); border-left:4px solid #3b82f6; padding:16px; margin-bottom:24px; border-radius:0 8px 8px 0;'>
            <div style='color:#60a5fa; font-weight:700; font-size:13px; margin-bottom:6px; letter-spacing:0.5px;'>🧠 AGENT-AUGMENTED MACHINE LEARNING (LATE FUSION)</div>
            <div style='color:#d4d4d8; font-size:13px; line-height:1.6;'>
                Sistem tidak lagi hanya mengandalkan data matematis. <b>Hermes Agent</b> baru saja memodifikasi probabilitas XGBoost berdasarkan kondisi dunia nyata. <br>
                <b>Cuaca/Konteks:</b> {agent_weather if agent_weather else 'Tidak ada data real-time.'} <br>
                <b>Alasan Agent:</b> {agent_reasoning if agent_reasoning else 'Menggunakan model dasar XGBoost tanpa penyesuaian.'}
            </div>
        </div>
        """, unsafe_allow_html=True)

        p1, p2, p3 = st.columns(3)
        with p1: st.markdown(prob_card("Home Win", model_prob_H, market_prob[2], edge_H, o_h, base_prob=base_prob_H), unsafe_allow_html=True)
        with p2: st.markdown(prob_card("Draw", model_prob_D, market_prob[1], edge_D, o_d, base_prob=base_prob_D), unsafe_allow_html=True)
        with p3: st.markdown(prob_card("Away Win", model_prob_A, market_prob[0], edge_A, o_a, base_prob=base_prob_A), unsafe_allow_html=True)
        
        # Regression exact score prediction
        if reg_home is not None and reg_away is not None:
            
            pred_h_round = int(round(pred_h_raw))
            pred_a_round = int(round(pred_a_raw))
            
            if pred_h_round > pred_a_round:
                win_text = f"👑 {home_team} Menang"
                win_color = "#3b82f6"
            elif pred_a_round > pred_h_round:
                win_text = f"👑 {away_team} Menang"
                win_color = "#a855f7"
            else:
                win_text = "⚖️ Hasil Seri (Draw)"
                win_color = "#f59e0b"
                
            st.markdown(f"""
            <div style='background:linear-gradient(90deg, #111113 0%, #17171c 100%); border:1px solid #1f1f23; border-radius:16px; padding:20px 32px; margin-top:24px; display:flex; justify-content:space-between; flex-wrap: wrap;; flex-wrap: wrap;; align-items:center; flex-wrap: wrap; gap:16px; box-shadow: 0 4px 20px rgba(0,0,0,0.2);'>
                <div>
                    <div style='font-size:12px; color:#3b82f6; font-weight:700; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:4px;'>🎯 Exact Score Prediction</div>
                    <div style='font-size:13px; color:#71717a;'>Powered by dual XGBoost Regressors</div>
                </div>
                <div style='text-align:right;'>
                    <div style='font-size:36px; font-weight:800; color:#fafafa; letter-spacing:-1px; margin-bottom:4px;'>
                        <span style='color:#a1a1aa; font-size:20px; margin-right:12px; font-weight:600;'>{home_team}</span> 
                        {pred_h_round} - {pred_a_round} 
                        <span style='color:#a1a1aa; font-size:20px; margin-left:12px; font-weight:600;'>{away_team}</span>
                    </div>
                    <div style='font-size:13px; font-weight:600; color:{win_color}; letter-spacing:0.5px;'>
                        {win_text} <span style='color:#52525b; font-weight:500; margin-left:8px;'>(xG: {pred_h_raw:.1f} - {pred_a_raw:.1f})</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        # ── GEMINI 2.5 FLASH INSIGHT (PUNDIT) ──
        if agent_data and 'pundit_analysis' in agent_data:
            st.markdown('<div class="section-title" style="margin-top: 40px; margin-bottom: 16px;">🤖 AI Analysis (Hermes x XGBoost)</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div style="background:#0f172a; border:1px solid #1e293b; border-radius:12px; padding:24px; margin-bottom: 24px;">
                <div style="color:#94a3b8; font-size:12px; margin-bottom:12px; font-family:monospace;">🤖 GEMINI 2.5 FLASH INSIGHT</div>
                <div style="color:#f8fafc; font-size:14px; line-height:1.7;">
                    {agent_data['pundit_analysis']}
                </div>
            </div>
            """, unsafe_allow_html=True)
        


        # Data Mining Stats
        st.markdown('<div class="section-title" style="margin-top:56px; margin-bottom:24px; padding-bottom:8px; border-bottom:1px solid #1f1f23;">⚙️ Model Input Features (Pre-Match Data)</div>', unsafe_allow_html=True)
        s1, s2 = st.columns(2)
        with s1:
            st.markdown(f"""
            <div style='background:#111113; border:1px solid #1f1f23; border-radius:12px; padding:24px; border-top:3px solid #3b82f6'>
                <div style='color:#a1a1aa; font-size:12px; font-weight:bold; text-transform:uppercase'>HOME STATISTICS</div>
                <div style='color:#fafafa; font-size:20px; font-weight:bold; margin-bottom:16px'>{home_team}</div>
                <div style='display:flex; justify-content:space-between; flex-wrap: wrap;; flex-wrap: wrap;'>
                    <div style='text-align:center'><div style='color:#3b82f6; font-size:24px; font-weight:bold'>{h_gs:.1f}</div><div style='color:#71717a; font-size:10px; margin-top:4px'>AVG GOALS</div></div>
                    <div style='text-align:center'><div style='color:#ef4444; font-size:24px; font-weight:bold'>{h_gc:.1f}</div><div style='color:#71717a; font-size:10px; margin-top:4px'>CONCEDED</div></div>
                    <div style='text-align:center'><div style='color:#10b981; font-size:24px; font-weight:bold'>{h_st:.1f}</div><div style='color:#71717a; font-size:10px; margin-top:4px'>SHOTS ON TARGET</div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with s2:
            st.markdown(f"""
            <div style='background:#111113; border:1px solid #1f1f23; border-radius:12px; padding:24px; border-top:3px solid #a855f7'>
                <div style='color:#a1a1aa; font-size:12px; font-weight:bold; text-transform:uppercase'>AWAY STATISTICS</div>
                <div style='color:#fafafa; font-size:20px; font-weight:bold; margin-bottom:16px'>{away_team}</div>
                <div style='display:flex; justify-content:space-between; flex-wrap: wrap;; flex-wrap: wrap;'>
                    <div style='text-align:center'><div style='color:#a855f7; font-size:24px; font-weight:bold'>{a_gs:.1f}</div><div style='color:#71717a; font-size:10px; margin-top:4px'>AVG GOALS</div></div>
                    <div style='text-align:center'><div style='color:#ef4444; font-size:24px; font-weight:bold'>{a_gc:.1f}</div><div style='color:#71717a; font-size:10px; margin-top:4px'>CONCEDED</div></div>
                    <div style='text-align:center'><div style='color:#10b981; font-size:24px; font-weight:bold'>{a_st:.1f}</div><div style='color:#71717a; font-size:10px; margin-top:4px'>SHOTS ON TARGET</div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)


    plotly_layout = dict(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#0c0c0f', font=dict(color='#a1a1aa', family='Inter'))
    axis_style = dict(gridcolor='#1a1a2e', color='#52525b', zerolinecolor='#1f1f23')
    fn = ['HomeTeam','AwayTeam','AvgGoals_H','AvgConceded_H','AvgShots_H','AvgGoals_A','AvgConceded_A','AvgShots_A','Odds_H','Odds_D','Odds_A']

    with tab_analytics:
        st.markdown('<div class="section-title">Feature Correlation Heatmap</div>', unsafe_allow_html=True)
        try:
            corr = pd.read_csv('feature_correlation.csv', index_col=0)
            if len(fn)+1 == len(corr.columns):
                corr.columns = fn + ['Result']
                corr.index = fn + ['Result']
            fig = go.Figure(go.Heatmap(z=corr.values, x=corr.columns, y=corr.index,
                colorscale=[[0,'#09090b'],[0.25,'#1a1a3a'],[0.5,'#27272a'],[0.75,'#3b4f8a'],[1,'#3b82f6']],
                text=np.round(corr.values,2), texttemplate='%{text}', textfont=dict(size=10,color='#fafafa'),
                showscale=False))
            fig.update_layout(**plotly_layout, height=550, margin=dict(t=24,b=80,l=120),
                xaxis=dict(tickangle=45, color='#a1a1aa'), yaxis=dict(color='#a1a1aa'))
            lc1, lc2, lc3 = st.columns([1, 6, 1])
            with lc2: st.plotly_chart(fig, use_container_width=True)
            st.caption("Heatmap ini menunjukkan korelasi antar fitur. Warna biru terang menunjukkan hubungan yang kuat.")
        except Exception as e:
            st.info(f"Correlation data unavailable: {e}")
            
        st.markdown('<div class="section-title" style="margin-top:32px">SHAP Feature Impact</div>', unsafe_allow_html=True)
        if not eval_metrics:
            st.info("Run train_model.py first to see SHAP analysis.")
        else:
            try:
                shap_vals = eval_metrics.get('shap_values')
                if shap_vals is not None:
                    sa = np.array(shap_vals)
                    nf = len(fn)
                    if sa.ndim==3: svc = sa[:,:,2].mean(axis=0) if sa.shape[2]>2 else sa[:,:,0].mean(axis=0)
                    elif sa.ndim==2: svc = sa[0,:] if sa.shape[1]==nf else sa.flatten()[:nf]
                    else: svc = sa.flatten()[:nf]
                    
                    ssi = np.argsort(np.abs(svc)); ssv = svc[ssi]; ssn = [fn[i] for i in ssi]
                    
                    bc = ['#3b82f6' if v>0 else '#ef4444' for v in ssv]
                    fig = go.Figure(go.Bar(x=ssv, y=ssn, orientation='h', marker=dict(color=bc, line=dict(width=0)),
                        text=[f'{v:+.3f}' for v in ssv], textposition='outside', textfont=dict(color='#a1a1aa',size=12)))
                    fig.update_layout(**plotly_layout, height=500, xaxis={**axis_style, 'title':'SHAP Value (Impact on Prediction)'},
                        yaxis=dict(color='#a1a1aa'), margin=dict(l=130,r=60,t=24,b=40))
                    lc1, lc2, lc3 = st.columns([1, 6, 1])
                    with lc2: st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"SHAP computation failed: {e}")

    with tab_diag:
        st.markdown("""
        <div style='background:linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(139, 92, 246, 0.05) 100%); border:1px solid rgba(59, 130, 246, 0.3); border-left:4px solid #3b82f6; padding:24px; margin-bottom:32px; border-radius:12px; backdrop-filter: blur(10px); box-shadow: 0 4px 20px rgba(0,0,0,0.2);'>
            <div style='display:flex; align-items:center; gap:12px; margin-bottom:12px;'>
                <div style='background:#3b82f6; color:white; width:28px; height:28px; border-radius:6px; display:flex; align-items:center; justify-content:center; font-size:16px; font-weight:bold; box-shadow: 0 2px 8px rgba(59,130,246,0.4);'>i</div>
                <div style='color:#60a5fa; font-weight:800; font-size:14px; letter-spacing:1px; text-transform:uppercase;'>Info Untuk Penguji (Global Evaluation)</div>
            </div>
            <div style='color:#d4d4d8; font-size:14px; line-height:1.7;'>
                Seluruh metrik dan grafik pada halaman <b>Model Diagnostics</b> ini (Leaderboard, Confusion Matrix, ROC) adalah hasil evaluasi performa model secara <b>Global & Historis</b> terhadap <b>7.000+ pertandingan</b>. <br>Grafik ini bersifat statis dan <b>TIDAK AKAN BERUBAH</b> saat Anda mengganti tim yang bertanding di menu utama. Fungsinya adalah sebagai bukti akademis untuk menunjukkan tingkat keakuratan algoritma XGBoost secara keseluruhan.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="section-title">Machine Learning Algorithm Leaderboard</div>', unsafe_allow_html=True)
        if eval_metrics and 'model_comparison' in eval_metrics:
            mc = eval_metrics['model_comparison']
            mc_df = pd.DataFrame([{
                'Algorithm': k,
                'Accuracy': v['mean'],
                'StdDev': v['std']
            } for k, v in mc.items()]).sort_values('Accuracy', ascending=True)
            
            # Highlight XGBoost
            colors = ['#3b82f6' if algo == 'XGBoost' else '#3f3f46' for algo in mc_df['Algorithm']]
            
            fig = go.Figure(go.Bar(
                x=mc_df['Accuracy'], 
                y=mc_df['Algorithm'], 
                orientation='h',
                marker=dict(color=colors, line=dict(width=0)),
                text=[f'{val*100:.1f}%' for val in mc_df['Accuracy']],
                textposition='outside',
                textfont=dict(color='#a1a1aa', size=12)
            ))
            fig.update_layout(**plotly_layout, height=400, margin=dict(l=130, r=60, t=24, b=40),
                xaxis={**axis_style, 'title':'Cross-Validation Accuracy (%)', 'range':[0, max(mc_df['Accuracy'])+0.1]},
                yaxis=dict(color='#a1a1aa'))
            lc1, lc2, lc3 = st.columns([1, 6, 1])
            with lc2: st.plotly_chart(fig, use_container_width=True)
            st.caption("Perbandingan akurasi 7 algoritma Machine Learning yang diuji secara *cross-validation*. XGBoost dipilih sebagai mesin utama karena memimpin klasemen.")
        else:
            st.info("Run train_model.py first to see model comparison.")
            
        st.markdown('<div class="section-title" style="margin-top:32px">Confusion Matrix</div>', unsafe_allow_html=True)
        if eval_metrics:
            cm = eval_metrics['confusion_matrix']
            cn = eval_metrics['class_names']
            cn_l = [{'A':'Away','D':'Draw','H':'Home'}.get(c,c) for c in cn]
            fig = go.Figure(go.Heatmap(z=cm, x=cn_l, y=cn_l,
                colorscale=[[0,'#09090b'],[0.5,'#1e3a5f'],[1,'#3b82f6']],
                text=cm, texttemplate='%{text}', textfont=dict(size=24,color='white'),
                hovertemplate='Actual: %{y}<br>Predicted: %{x}<br>Count: %{z}<extra></extra>', showscale=False))
            fig.update_layout(**plotly_layout, height=450, margin=dict(t=24,b=60),
                xaxis=dict(title='Predicted', **axis_style),
                yaxis=dict(title='Actual', autorange='reversed', **axis_style))
            lc1, lc2, lc3 = st.columns([1, 4, 1])
            with lc2: st.plotly_chart(fig, use_container_width=True)
            total = cm.sum(); correct = np.trace(cm)
            st.success(f"**Model Accuracy:** {correct}/{total} correct predictions ({correct/total*100:.1f}%) on unseen test data.")
        else: st.info("Run train_model.py first.")
        
        st.markdown('<div class="section-title" style="margin-top:32px">ROC Curve</div>', unsafe_allow_html=True)
        if eval_metrics:
            from sklearn.metrics import roc_curve, auc
            ytb = eval_metrics['y_test_bin']; ypp = eval_metrics['y_pred_proba']
            cn_m = {'A':'Away','D':'Draw','H':'Home'}
            roc_c = ['#3b82f6','#f59e0b','#a855f7']
            fig = go.Figure()
            for i, (c, col) in enumerate(zip(cn, roc_c)):
                fpr, tpr, _ = roc_curve(ytb[:,i], ypp[:,i]); a_ = auc(fpr,tpr)
                fig.add_trace(go.Scatter(x=fpr, y=tpr, mode='lines', name=f'{cn_m.get(c,c)} (AUC={a_:.3f})',
                    line=dict(color=col,width=3)))
            fig.add_trace(go.Scatter(x=[0,1], y=[0,1], mode='lines', name='Random',
                line=dict(color='#3f3f46',width=2,dash='dash'), showlegend=False))
            fig.update_layout(**plotly_layout, height=450, margin=dict(t=24,b=60),
                xaxis=dict(title='False Positive Rate', **axis_style),
                yaxis=dict(title='True Positive Rate', **axis_style))
            lc1, lc2, lc3 = st.columns([1, 4, 1])
            with lc2: st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('<div class="section-title" style="margin-top:32px">Learning Curve</div>', unsafe_allow_html=True)
        if eval_metrics and 'learning_curve' in eval_metrics:
            lc = eval_metrics['learning_curve']
            ts, tr_m, tr_s, vl_m, vl_s = np.array(lc['train_sizes']), np.array(lc['train_mean']), np.array(lc['train_std']), np.array(lc['val_mean']), np.array(lc['val_std'])
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=ts, y=tr_m, mode='lines+markers', name='Training Score', line=dict(color='#3b82f6', width=3)))
            fig.add_trace(go.Scatter(x=np.concatenate([ts, ts[::-1]]), y=np.concatenate([tr_m - tr_s, (tr_m + tr_s)[::-1]]), fill='toself', fillcolor='rgba(59,130,246,0.1)', line=dict(color='rgba(255,255,255,0)'), showlegend=False))
            fig.add_trace(go.Scatter(x=ts, y=vl_m, mode='lines+markers', name='Cross-validation Score', line=dict(color='#a855f7', width=3)))
            fig.add_trace(go.Scatter(x=np.concatenate([ts, ts[::-1]]), y=np.concatenate([vl_m - vl_s, (vl_m + vl_s)[::-1]]), fill='toself', fillcolor='rgba(168,85,247,0.1)', line=dict(color='rgba(255,255,255,0)'), showlegend=False))
            fig.update_layout(**plotly_layout, height=450, margin=dict(t=24,b=60), xaxis=dict(title='Training Examples', **axis_style), yaxis=dict(title='Accuracy Score', **axis_style))
            lc1, lc2, lc3 = st.columns([1, 4, 1])
            with lc2: st.plotly_chart(fig, use_container_width=True)

    with tab_sent:
        st.markdown('<div class="section-title">Real-time NLP Sentiment Analysis</div>', unsafe_allow_html=True)
        if not GEMINI_API_KEY:
            st.warning("GEMINI_API_KEY is required for Sentiment Analysis.")
        else:
            try:
                import google.generativeai as genai
                genai.configure(api_key=GEMINI_API_KEY)
                gmodel = genai.GenerativeModel('gemini-2.5-flash')
                
                with st.spinner("Scraping live news & analyzing NLP sentiment..."):
                    home_news = fetch_news(home_team)
                    away_news = fetch_news(away_team)
                    
                    if not home_news and not away_news:
                        st.info("No recent news found for these teams.")
                    else:
                        prompt_h = f"Berdasarkan 3 berita terbaru tentang {home_team}: {home_news}. Tentukan sentimen publik (Pilih satu: POSITIF, NEGATIF, atau NETRAL) dan berikan 1 kalimat singkat alasan/fakta dari berita tersebut dalam bahasa Indonesia."
                        prompt_a = f"Berdasarkan 3 berita terbaru tentang {away_team}: {away_news}. Tentukan sentimen publik (Pilih satu: POSITIF, NEGATIF, atau NETRAL) dan berikan 1 kalimat singkat alasan/fakta dari berita tersebut dalam bahasa Indonesia."
                        
                        res_h = gmodel.generate_content(prompt_h).text.strip()
                        res_a = gmodel.generate_content(prompt_a).text.strip()
                        
                        badge_h = get_sentiment_badge(res_h)
                        badge_a = get_sentiment_badge(res_a)
                        
                        desc_h = res_h.split('\n')[-1].replace('POSITIF','').replace('NEGATIF','').replace('NETRAL','').strip(':.- ')
                        desc_a = res_a.split('\n')[-1].replace('POSITIF','').replace('NEGATIF','').replace('NETRAL','').strip(':.- ')
                        
                        s1, s2 = st.columns(2)
                        with s1:
                            st.markdown(f"""
                            <div style='background:#111113; border:1px solid #1f1f23; border-radius:12px; padding:24px; height:100%'>
                                <h3 style='margin:0 0 16px 0; color:#fafafa'>{home_team}</h3>
                                <div style='font-size:18px; font-weight:bold; margin-bottom:16px'>{badge_h}</div>
                                <p style='color:#a1a1aa; font-size:14px; line-height:1.6'><b>Analisis AI:</b> {desc_h}</p>
                                <div style='margin-top:24px; padding-top:16px; border-top:1px dashed #27272a'>
                                    <div style='font-size:11px; color:#52525b; text-transform:uppercase; margin-bottom:8px'>Latest Headlines</div>
                                    <ul style='color:#71717a; font-size:12px; padding-left:16px'>
                                        {"".join([f"<li>{n}</li>" for n in home_news])}
                                    </ul>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        with s2:
                            st.markdown(f"""
                            <div style='background:#111113; border:1px solid #1f1f23; border-radius:12px; padding:24px; height:100%'>
                                <h3 style='margin:0 0 16px 0; color:#fafafa'>{away_team}</h3>
                                <div style='font-size:18px; font-weight:bold; margin-bottom:16px'>{badge_a}</div>
                                <p style='color:#a1a1aa; font-size:14px; line-height:1.6'><b>Analisis AI:</b> {desc_a}</p>
                                <div style='margin-top:24px; padding-top:16px; border-top:1px dashed #27272a'>
                                    <div style='font-size:11px; color:#52525b; text-transform:uppercase; margin-bottom:8px'>Latest Headlines</div>
                                    <ul style='color:#71717a; font-size:12px; padding-left:16px'>
                                        {"".join([f"<li>{n}</li>" for n in away_news])}
                                    </ul>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Sentiment Analysis failed: {e}")
