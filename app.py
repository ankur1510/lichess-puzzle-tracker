import streamlit as st
import streamlit.components.v1 as components
import requests, json, datetime
from collections import defaultdict

LICHESS_TOKEN = "lip_iNKvkOifzZmJh49Xd62v"
USERNAME = "fancy_pencil"
HEADERS = {"Authorization": f"Bearer {LICHESS_TOKEN}"}

# Page Configuration
st.set_page_config(page_title="Puzzle Analytics Dashboard", page_icon="♟️", layout="wide")

# --- Custom CSS Injection for Modern UI ---
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    h1, h2, h3, h4 { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #1e293b; }
    .metric-container {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 16px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        text-align: center;
    }
    .metric-value { font-size: 24px; font-weight: 700; color: #3b82f6; margin-top: 5px; }
    .metric-label { font-size: 13px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }
    table tr:hover { background-color: #f1f5f9 !important; transition: background 0.2s ease; }
    </style>
""", unsafe_allow_html=True)

# Dashboard Header
st.title("♟️ Puzzle Training Analytics Dashboard")
st.caption("Track daily puzzle volume, performance trends, and tactical theme strengths anonymously.")

# --- Filter Section ---
st.markdown("### ⏳ Filter Options")
col_f, col_e = st.columns([1, 3])
with col_f:
    tf = st.selectbox("Date Range", ["1 Week", "15 Days", "Current Month", "Last N Days", "Custom Date Range"], index=0)

today = datetime.date.today()
if tf == "1 Week": start_date, end_date = today - datetime.timedelta(days=6), today
elif tf == "15 Days": start_date, end_date = today - datetime.timedelta(days=14), today
elif tf == "Current Month": start_date, end_date = today.replace(day=1), today
elif tf == "Last N Days":
    n_days = col_e.number_input("Days", min_value=1, value=30)
    start_date, end_date = today - datetime.timedelta(days=n_days-1), today
else:
    dr = col_e.date_input("Select Dates", [today - datetime.timedelta(days=14), today])
    start_date, end_date = (dr[0], dr[1]) if len(dr) == 2 else (dr[0], today)

@st.cache_data(ttl=300)
def get_act():
    acts = []
    try:
        r = requests.get("https://lichess.org/api/puzzle/activity?max=1000", headers=HEADERS, stream=True, timeout=20)
        if r.status_code == 200:
            for line in r.iter_lines():
                if line: acts.append(json.loads(line.decode("utf-8")))
    except: pass
    return acts

with st.spinner("Loading complete Lichess puzzle history..."):
    act_data = get_act()

daily_stats = defaultdict(lambda: {"solved": 0, "total": 0})
daily_themes = defaultdict(lambda: defaultdict(lambda: {"att": 0, "sol": 0, "rat_sum": 0}))
range_themes = defaultdict(lambda: {"att": 0, "sol": 0, "rat_sum": 0})

for item in act_data:
    ts = item.get("date", 0) / 1000
    if ts > 0:
        p_date = datetime.datetime.fromtimestamp(ts).date()
        if start_date <= p_date <= end_date:
            d_str = p_date.strftime("%Y-%m-%d")
            win = 1 if item.get("win") else 0
            daily_stats[d_str]["total"] += 1
            daily_stats[d_str]["solved"] += win
            
            puz = item.get("puzzle", {})
            rat = puz.get("rating", 1500)
            themes = puz.get("themes", [])
            
            if themes:
                main_th = themes[0]
                daily_themes[d_str][main_th]["att"] += 1
                daily_themes[d_str][main_th]["sol"] += win
                daily_themes[d_str][main_th]["rat_sum"] += rat
                range_themes[main_th]["att"] += 1
                range_themes[main_th]["sol"] += win
                range_themes[main_th]["rat_sum"] += rat

f_days = sorted(daily_stats.keys())
l_day = [datetime.datetime.strptime(d, "%Y-%m-%d").strftime("%b %d, %Y") for d in f_days]
a_day = [daily_stats[d]["total"] for d in f_days]
tot_puz_att = sum(a_day)
tot_puz_sol = sum(daily_stats[d]["solved"] for d in f_days)
overall_acc = round((tot_puz_sol / tot_puz_att) * 100, 1) if tot_puz_att > 0 else 0

# --- Top Summary Metric Cards ---
st.markdown("---")
m1, m2, m3 = st.columns(3)
with m1:
    st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">Total Attempted</div>
            <div class="metric-value" style="color: #6366f1;">{tot_puz_att}</div>
        </div>
    """, unsafe_allow_html=True)
with m2:
    st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">Total Solved</div>
            <div class="metric-value" style="color: #22c55e;">{tot_puz_sol}</div>
        </div>
    """, unsafe_allow_html=True)
with m3:
    st