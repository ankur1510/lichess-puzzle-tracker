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
st.title(f"♟️	Puzzle Analytics Dashboard")
st.caption("Track daily puzzle volume, performance trends, and tactical theme strengths.")

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
    st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">Overall Accuracy</div>
            <div class="metric-value" style="color: #3b82f6;">{overall_acc}%</div>
        </div>
    """, unsafe_allow_html=True)
st.markdown("---")

sel_date = st.query_params.get("date", None)
if sel_date not in daily_themes:
    sel_date = None

active_theme_dict = daily_themes[sel_date] if sel_date else range_themes
sorted_themes = sorted(active_theme_dict.items(), key=lambda x: x[1]["att"], reverse=True)

t_labels = [t.capitalize() for t, d in sorted_themes]
t_att = [d["att"] for t, d in sorted_themes]
t_sol = [d["sol"] for t, d in sorted_themes]
tot_th_att = sum(t_att)
tot_th_sol = sum(t_sol)

c_d1 = json.dumps({"labels": l_day, "datasets": [{"label": "Attempted", "data": a_day, "borderColor": "#8b5cf6", "backgroundColor": "rgba(139,92,246,0.15)", "tension": 0.4, "fill": True}]})
c_d2 = json.dumps({"labels": t_labels, "datasets": [{"label": "Attempted", "data": t_att, "backgroundColor": "#cbd5e1"}, {"label": "Solved", "data": t_sol, "backgroundColor": "#3b82f6"}]})

chart_height = max(250, len(t_labels) * 28)

# --- Charts Section ---
html_code = f"""
<script src='https://cdn.jsdelivr.net/npm/chart.js'></script>
<script src='https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2'></script>
<div style="display:flex; gap:20px; font-family:sans-serif;">
  <div style="flex:1; background:#ffffff; padding:18px; border-radius:12px; border:1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);">
    <h4 style="margin:0 0 12px 0; color:#1e293b; font-size:15px;">📅 Day-Wise Volume Curve</h4>
    <div style="height:260px;"><canvas id='c1'></canvas></div>
  </div>
  <div style="flex:1; background:#ffffff; padding:18px; border-radius:12px; border:1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);">
    <h4 style="margin:0 0 12px 0; color:#1e293b; font-size:15px;">🎯 Main Themes Performance</h4>
    <div style="height:260px; overflow-y:auto; overflow-x:auto; border:1px solid #f1f5f9; border-radius:6px;">
      <div style="width:100%; height:{chart_height}px; min-width:350px;">
        <canvas id='c2'></canvas>
      </div>
    </div>
  </div>
</div>
<script>
Chart.register(ChartDataLabels);
new Chart(document.getElementById('c1'), {{
    type: 'line', 
    data: {c_d1}, 
    options: {{
        responsive: true, 
        maintainAspectRatio: false,
        plugins: {{ datalabels: {{ display: false }} }}
    }}
}});
new Chart(document.getElementById('c2'), {{
    type: 'bar', 
    data: {c_d2}, 
    options: {{
        indexAxis: 'y', 
        responsive: true, 
        maintainAspectRatio: false,
        plugins: {{
            datalabels: {{
                anchor: 'end',
                align: 'end',
                color: '#1e293b',
                font: {{ weight: 'bold', size: 11 }}
            }}
        }},
        scales: {{
            x: {{ beginAtZero: true, grace: '15%' }}
        }}
    }}
}});
</script>
"""
components.html(html_code, height=330)
st.markdown("---")

# --- Tables Section ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("📅 Daily Training Log")
    st.caption("💡 Click any date below to inspect that specific day's theme performance on the right.")
    rows = ""
    for d in reversed(f_days):
        att, sol = daily_stats[d]["total"], daily_stats[d]["solved"]
        if att > 0:
            acc = round((sol / att) * 100, 1)
            col = "#22c55e" if acc >= 70 else "#f59e0b" if acc >= 50 else "#ef4444"
            dt = datetime.datetime.strptime(d, "%Y-%m-%d").strftime("%b %d, %Y")
            bg = "#eef2ff" if d == sel_date else "transparent"
            rows += f"<tr style='background:{bg};'><td style='padding:10px;border-bottom:1px solid #f1f5f9;'><a href='?date={d}' target='_self' style='text-decoration:none;color:#2563eb;font-weight:600;'>🔗 {dt}</a></td><td style='padding:10px;'>{att}</td><td style='padding:10px;'>{sol}</td><td style='padding:10px;color:{col};font-weight:bold;'>{acc}%</td></tr>"
    st.markdown(f"<div style='background:#ffffff;border:1px solid #e2e8f0;border-radius:10px;padding:10px;box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);'><table style='width:100%;font-family:sans-serif;font-size:14px;text-align:left;'><tr style='background:#f8fafc;color:#475569;'><th style='padding:10px;'>Date</th><th>Attempted</th><th>Solved</th><th>Accuracy</th></tr>{rows}</table></div>", unsafe_allow_html=True)

with col2:
    if sel_date:
        dt_disp = datetime.datetime.strptime(sel_date, "%Y-%m-%d").strftime("%b %d, %Y")
        p_att, p_sol = daily_stats[sel_date]["total"], daily_stats[sel_date]["solved"]
        sub_title = f"🎯 Theme Breakdown for {dt_disp} ({p_att} Puzzles)"
        reset_btn = True
    else:
        p_att, p_sol = tot_puz_att, tot_puz_sol
        sub_title = f"🎯 Filtered Theme Breakdown ({p_att} Puzzles)"
        reset_btn = False
        
    st.subheader(sub_title)
    if reset_btn:
        if st.button("🔄 Show All Dates in Range"):
            st.query_params.clear()
            st.rerun()
    else:
        st.caption("💡 Overall stats across the chosen date range.")
        
    t_rows = ""
    for t, det in sorted_themes:
        att, sol = det["att"], det["sol"]
        rat = round(det["rat_sum"] / att) if att > 0 else "N/A"
        if att > 0:
            acc = round((sol / att) * 100, 1)
            col = "#22c55e" if acc >= 70 else "#f59e0b" if acc >= 50 else "#ef4444"
            t_rows += f"<tr><td style='padding:10px;border-bottom:1px solid #f1f5f9;text-transform:capitalize;'><b>{t}</b></td><td style='padding:10px;'>{att}</td><td style='padding:10px;'>{sol}</td><td style='padding:10px;color:{col};font-weight:bold;'>{acc}%</td><td style='padding:10px;'>{rat}</td></tr>"
    
    tot_acc = round((tot_th_sol / tot_th_att) * 100, 1) if tot_th_att > 0 else 0
    t_rows += f"<tr style='background:#f8fafc;font-weight:bold;'><td style='padding:10px;'>TOTAL</td><td style='padding:10px;'>{tot_th_att}</td><td style='padding:10px;'>{tot_th_sol}</td><td style='padding:10px;'>{tot_acc}%</td><td style='padding:10px;'>-</td></tr>"
    
    table_html = (
        "<div style='background:#ffffff;border:1px solid #e2e8f0;border-radius:10px;padding:10px;box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);max-height:430px;overflow-y:auto;'>"
        "<table style='width:100%;font-family:sans-serif;font-size:14px;text-align:left;'>"
        "<tr style='background:#f8fafc;position:sticky;top:0;color:#475569;z-index:2;'>"
        "<th style='padding:10px;'>Main Theme</th><th style='padding:10px;'>Attempted</th><th style='padding:10px;'>Solved</th><th style='padding:10px;'>Accuracy</th><th style='padding:10px;'>Avg Rating</th>"
        f"</tr>{t_rows}</table></div>"
    )
    st.markdown(table_html, unsafe_allow_html=True)
