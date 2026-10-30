"""Local procurement analytics. Run: streamlit run app.py"""
import io
import math
import re
import html
import json
import hashlib
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

st.set_page_config(page_title="Procurement | Supply Chain Control Center", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

SPEND = "Ytd Sep26 12mths PO Spends (USD)"
QTY = "Ytd Sep26 12mths PO Qty (Kgs)"
FILTERS = [
    ("Dyes / Chemical", "Dyes/Chem"), ("Plant Region", "Plant Region"),
    ("Initiative Type", "Initiative Type"), ("Sub Category", "Sub Category"),
    ("Plant Manager", "Catergory Manager"), ("Plant", "Plant"),
    ("Plant Code", "Mat+Plant"), ("Material Name", "Material Name"),
    ("Material Code", "Material"),
]
MONTHS = [(datetime(2026 + (9+i)//12, (9+i)%12+1, 1).strftime('%b %y')) for i in range(12)]
REGION_COORDS = {
    "North America": (39, -101), "South America": (-15, -60), "Latin America": (-15, -65),
    "EMEA": (47, 20), "Pakistan": (30, 69), "India": (22, 79),
    "South Asia": (17, 81), "North Asia": (51, 106), "Greater China": (35, 105),
    "South East Asia": (7, 112), "Rest of World": (0, 0),
}

st.markdown("""<style>
:root{--navy:#1e1b4b;--ink:#172033;--muted:#64748b;--purple:#4f46e5}
html,body,[data-testid="stApp"]{font-family:Inter,ui-sans-serif,system-ui,sans-serif}
[data-testid="stAppViewContainer"]{background:#f9fafb;color:#1f2937}
[data-testid="stHeader"]{background:#f9fafb00;height:2.5rem}
[data-testid="stSidebar"]{background:#1e1b4b!important;border-right:1px solid #312e81;min-width:264px}
[data-testid="stSidebar"]>div:first-child{padding-top:.6rem}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p{font-size:11px!important;font-weight:600!important;color:#c7d2fe!important}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"]{margin-bottom:3px}
[data-testid="stSidebar"] [data-baseweb="select"]>div{background:#312e81!important;border:1px solid #433878!important;border-radius:8px!important;min-height:34px!important}
[data-testid="stSidebar"] [data-baseweb="select"] *{color:#fff!important;font-size:12px}
[data-testid="stSidebar"] [data-baseweb="tag"]{background:#4f46e5!important}
[data-testid="stSidebar"] [data-testid="stFileUploader"]{border:1px dashed #6366f1;border-radius:9px}
[data-testid="stSidebar"] [data-testid="stFileUploader"] *{color:#c7d2fe!important}
[data-testid="stSidebar"] .stButton>button{border-radius:7px;background:#3730a3;color:#fff;border:1px solid #5148a8;min-height:32px;font-size:12px}
[data-testid="stSidebar"] .stButton>button:hover{background:#4f46e5;color:#fff}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p{color:#a5b4fc!important;font-size:10px!important}
[data-testid="stSidebar"] hr{border-color:#373078}
.block-container{padding-top:.5rem;max-width:1660px;padding-left:1.7rem;padding-right:1.7rem;padding-bottom:4rem}
h1{color:#111827;font-size:1.24rem!important;font-weight:760!important;letter-spacing:-.025em}
h2,h3{color:#1f2937;letter-spacing:-.02em}
h3{font-size:1rem!important;font-weight:750!important}
[data-testid="stMetric"]{background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:21px 19px;box-shadow:0 2px 5px #0f172a08;min-height:136px}
[data-testid="stMetricLabel"] p{color:#64748b;font-size:.74rem;font-weight:700;text-transform:uppercase;letter-spacing:.04em}
[data-testid="stMetricValue"]{color:#312e81;font-size:clamp(1.3rem,2vw,2rem);font-weight:800}
[data-testid="stVerticalBlockBorderWrapper"]>div{border-color:#e5e7eb!important;border-radius:12px!important;background:#fff;box-shadow:0 1px 4px #0f172a08}
[data-testid="stPlotlyChart"]{border-radius:9px;overflow:hidden}
[data-testid="stDataFrame"]{border:1px solid #e5e7eb;border-radius:9px;overflow:hidden}
[data-testid="stExpander"]{background:#fff;border:1px solid #e5e7eb;border-radius:10px}
.stDownloadButton>button{background:#047857;color:white;border:0;border-radius:8px}
.stDownloadButton>button:hover{background:#059669;color:white}
.small-note{font-size:12px;color:#64748b;margin-top:-.4rem;margin-bottom:1.2rem}
.nav-label{font-size:10px;font-weight:800;letter-spacing:.11em;color:#a5b4fc!important;margin:16px 0 8px}
.nav-item{display:block;padding:9px 11px;margin:5px 0;background:#312e81a8;border:1px solid #373078;border-radius:7px;color:#e0e7ff!important;text-decoration:none!important;font-size:12px;font-weight:650}
.nav-item:hover{background:#4338ca;color:#fff!important}
.brand{display:flex;gap:10px;align-items:center;padding:14px 0 20px;border-bottom:1px solid #373078;margin-bottom:17px}
.brand-icon{font-size:25px;color:#a5b4fc}
.brand-name{font-size:14px;font-weight:800;color:white}
.brand-sub{font-size:10px;color:#a5b4fc;letter-spacing:.02em}
.page-head{display:flex;justify-content:space-between;align-items:center;background:white;padding:19px 21px;border:1px solid #e5e7eb;border-radius:12px;box-shadow:0 1px 3px #0f172a08;margin-bottom:17px}
.page-head h2{font-size:19px;font-weight:800;margin:0;color:#111827}
.page-head p{font-size:12px;color:#64748b;margin:5px 0 0}
.head-badge{font-size:10px;background:#eef2ff;color:#4338ca;padding:7px 11px;border-radius:7px;font-weight:750}
.section-heading{font-size:14px;font-weight:800;color:#273149;margin:21px 0 12px}
.insight{background:linear-gradient(90deg,#fffbeb,#fff7ed);border:1px solid #fcd9a4;border-radius:11px;padding:14px 18px;margin:12px 0 18px;font-size:12px;color:#92400e}
.insight b{font-size:11px;letter-spacing:.05em}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{gap:.43rem}
@media(max-width:900px){.block-container{padding-left:1rem;padding-right:1rem}.page-head{padding:14px}.head-badge{display:none}}
</style>""", unsafe_allow_html=True)

# The sample records are embedded directly so this application is truly single-file.
SAMPLE_DATA = [{'Mat+Plant': '286009308125811', 'Material': 28600930812, 'Material Name': 'Ultraphor PWC R pdr 0020', 'Plant': '5811', 'Plant Region': 'North America', 'Sub Category': 'Process & OBA Chemicals', 'Silicones': 'Process & OBA', 'Catergory Manager': 'Ben Mo', 'Dyes/Chem': 'Chemicals', 'Material Classification': 'Non_Index', 'Ytd Sep26 12mths PO Qty (Kgs)': 460000, 'Ytd Sep26 12mths PO Spends (USD)': 8199069, 'Ytd Sep26 Avg Unit Px': 17.824063, 'Stage Gate': '4-Go Live', 'Probability of Success': 1.0, "July- Sep26 Q4' (Q4 '26 PO Qty)": 80000, "July- Sep26 Q4' (Q4 '26 PO Spend)": 1449063, "July- Sep26 Q4' (Q4 26 Avg Unit Px)": 18.113287, 'Baseline PO price for FY27 Savings': 18.113287, 'Explain exceptions': None, 'FY26 Annualised Vol': 460000, 'FY26 Annualised Spends (Adjusted Price)': 8332111.82, 'Savings Start Month': '2027-01-01', 'Carry over or New': 'New', 'Initiative Type': 'New/alternative source/vendor', 'Project Name/Supplier': 'Hongda', 'No Blank': 'NO', 'AOP27 Mkt Px Change $ - increase / (decrease)': None, 'AOP27 Productivity Savings $/kg - (decrease)': -3.0, 'AOP27 Final Price': 15.113287, 'AOP27 Volume\n(Vol can be changed)': 460000, 'AOP27 Spends': 6952111.82, 'Spends Delta (Fav) / Unfav': -1380000.0, 'Volume Impact': 0.0, 'Market Effect': 0.0, 'Annual Productivity': -1380000.0, 'Annual Productivity ( in +ve)': 1.38, 'check': 0.0, 'Oct 26 (Vol)': 38333.333333, 'Nov 26 (Vol)': 38333.333333, 'Dec 26 (Vol)': 38333.333333, 'Jan 27 (Vol)': 38333.333333, 'Feb 27 (Vol)': 38333.333333, 'Mar 27 (Vol)': 38333.333333, 'Apr 27 (Vol)': 38333.333333, 'May 27 (Vol)': 38333.333333, 'Jun 27 (Vol)': 38333.333333, 'Jul 27 (Vol)': 38333.333333, 'Aug 27 (Vol)': 38333.333333, 'Sep 27 (Vol)': 38333.333333, 'Oct 26 (Saving)': 0.0, 'Nov 26 (Saving)': 0.0, 'Dec 26 (Saving)': 0.0, 'Jan 27 (Saving)': 115000.0, 'Feb 27 (Saving)': 115000.0, 'Mar 27 (Saving)': 115000.0, 'Apr 27 (Saving)': 115000.0, 'May 27 (Saving)': 115000.0, 'Jun 27 (Saving)': 115000.0, 'Jul 27 (Saving)': 115000.0, 'Aug 27 (Saving)': 115000.0, 'Sep 27 (Saving)': 115000.0, 'Actual Savings (YTD)': None}, {'Mat+Plant': '2417472104', 'Material': 241747, 'Material Name': 'Perfluorhexylethylmethacrylat', 'Plant': '2104', 'Plant Region': 'EMEA', 'Sub Category': 'Fluoro Chemicals', 'Silicones': 'Flouro Chem', 'Catergory Manager': 'Charles Allotey', 'Dyes/Chem': 'Chemicals', 'Material Classification': 'Non_Index', 'Ytd Sep26 12mths PO Qty (Kgs)': 203600, 'Ytd Sep26 12mths PO Spends (USD)': 9425250, 'Ytd Sep26 Avg Unit Px': 46.292976, 'Stage Gate': '4-Go Live', 'Probability of Success': 1.0, "July- Sep26 Q4' (Q4 '26 PO Qty)": 82000, "July- Sep26 Q4' (Q4 '26 PO Spend)": 3765713, "July- Sep26 Q4' (Q4 26 Avg Unit Px)": 45.923329, 'Baseline PO price for FY27 Savings': 45.923329, 'Explain exceptions': None, 'FY26 Annualised Vol': 203600, 'FY26 Annualised Spends (Adjusted Price)': 9349990.0, 'Savings Start Month': '2026-04-01', 'Carry over or New': 'Carry over', 'Initiative Type': 'Respecification', 'Project Name/Supplier': 'Zhongfu', 'No Blank': 'NO', 'AOP27 Mkt Px Change $ - increase / (decrease)': None, 'AOP27 Productivity Savings $/kg - (decrease)': -2.98, 'AOP27 Final Price': 42.943329, 'AOP27 Volume\n(Vol can be changed)': 203600, 'AOP27 Spends': 8743261.98, 'Spends Delta (Fav) / Unfav': -606728.02, 'Volume Impact': 0.0, 'Market Effect': 0.0, 'Annual Productivity': -606728.02, 'Annual Productivity ( in +ve)': 0.606728, 'check': 0.0, 'Oct 26 (Vol)': 16966.666667, 'Nov 26 (Vol)': 16966.666667, 'Dec 26 (Vol)': 16966.666667, 'Jan 27 (Vol)': 16966.666667, 'Feb 27 (Vol)': 16966.666667, 'Mar 27 (Vol)': 16966.666667, 'Apr 27 (Vol)': 16966.666667, 'May 27 (Vol)': 16966.666667, 'Jun 27 (Vol)': 16966.666667, 'Jul 27 (Vol)': 16966.666667, 'Aug 27 (Vol)': 16966.666667, 'Sep 27 (Vol)': 16966.666667, 'Oct 26 (Saving)': 50560.666667, 'Nov 26 (Saving)': 50560.666667, 'Dec 26 (Saving)': 50560.666667, 'Jan 27 (Saving)': 50560.666667, 'Feb 27 (Saving)': 50560.666667, 'Mar 27 (Saving)': 50560.666667, 'Apr 27 (Saving)': 0.0, 'May 27 (Saving)': 0.0, 'Jun 27 (Saving)': 0.0, 'Jul 27 (Saving)': 0.0, 'Aug 27 (Saving)': 0.0, 'Sep 27 (Saving)': 0.0, 'Actual Savings (YTD)': None}, {'Mat+Plant': '2897975504', 'Material': 289797, 'Material Name': 'FORMAZANE BLUE F-R MOIST', 'Plant': '5504', 'Plant Region': 'South East Asia', 'Sub Category': 'Reactive Dyes & Intermediates', 'Silicones': 'Reactive Dyes', 'Catergory Manager': 'Bhavesh Thakkar', 'Dyes/Chem': 'Dyes', 'Material Classification': 'Non_Index', 'Ytd Sep26 12mths PO Qty (Kgs)': 1161557, 'Ytd Sep26 12mths PO Spends (USD)': 7550181, 'Ytd Sep26 Avg Unit Px': 6.500052, 'Stage Gate': '4-Go Live', 'Probability of Success': 1.0, "July- Sep26 Q4' (Q4 '26 PO Qty)": 254268, "July- Sep26 Q4' (Q4 '26 PO Spend)": 1814778, "July- Sep26 Q4' (Q4 26 Avg Unit Px)": 7.137265, 'Baseline PO price for FY27 Savings': 7.137265, 'Explain exceptions': None, 'FY26 Annualised Vol': 1161557, 'FY26 Annualised Spends (Adjusted Price)': 8290340.23, 'Savings Start Month': '2026-10-01', 'Carry over or New': 'New', 'Initiative Type': 'Bulk Buying', 'Project Name/Supplier': 'Ambica', 'No Blank': 'NO', 'AOP27 Mkt Px Change $ - increase / (decrease)': 0.5, 'AOP27 Productivity Savings $/kg - (decrease)': -0.4, 'AOP27 Final Price': 7.237265, 'AOP27 Volume\n(Vol can be changed)': 1161557, 'AOP27 Spends': 8406495.23, 'Spends Delta (Fav) / Unfav': 116155.0, 'Volume Impact': 0.0, 'Market Effect': 580778.5, 'Annual Productivity': -464622.8, 'Annual Productivity ( in +ve)': 0.464623, 'check': 0.0, 'Oct 26 (Vol)': 96796.416667, 'Nov 26 (Vol)': 96796.416667, 'Dec 26 (Vol)': 96796.416667, 'Jan 27 (Vol)': 96796.416667, 'Feb 27 (Vol)': 96796.416667, 'Mar 27 (Vol)': 96796.416667, 'Apr 27 (Vol)': 96796.416667, 'May 27 (Vol)': 96796.416667, 'Jun 27 (Vol)': 96796.416667, 'Jul 27 (Vol)': 96796.416667, 'Aug 27 (Vol)': 96796.416667, 'Sep 27 (Vol)': 96796.416667, 'Oct 26 (Saving)': 38718.566667, 'Nov 26 (Saving)': 38718.566667, 'Dec 26 (Saving)': 38718.566667, 'Jan 27 (Saving)': 38718.566667, 'Feb 27 (Saving)': 38718.566667, 'Mar 27 (Saving)': 38718.566667, 'Apr 27 (Saving)': 38718.566667, 'May 27 (Saving)': 38718.566667, 'Jun 27 (Saving)': 38718.566667, 'Jul 27 (Saving)': 38718.566667, 'Aug 27 (Saving)': 38718.566667, 'Sep 27 (Saving)': 38718.566667, 'Actual Savings (YTD)': None}]

@st.cache_data(show_spinner=False, max_entries=5)
def load_dataset(file_bytes=None, filename=""):
    if file_bytes is None:
        frame = pd.DataFrame(SAMPLE_DATA)
    elif filename.lower().endswith('.csv'):
        try:
            frame = pd.read_csv(io.BytesIO(file_bytes), low_memory=False, dtype={"Material": "string", "Mat+Plant": "string", "Plant": "string"})
        except UnicodeDecodeError:
            frame = pd.read_csv(io.BytesIO(file_bytes), encoding="latin-1", low_memory=False)
    else:
        engine = "xlrd" if filename.lower().endswith('.xls') else "openpyxl"
        frame = pd.read_excel(io.BytesIO(file_bytes), engine=engine, dtype={"Material": "string", "Mat+Plant": "string", "Plant": "string"})
    frame.columns = [str(c).strip() for c in frame.columns]
    for _, col in FILTERS:
        if col not in frame:
            frame[col] = "Unassigned"
        frame[col] = frame[col].astype("string").fillna("Unassigned").str.strip().replace("", "Unassigned")
    for col in [SPEND, QTY]:
        if col not in frame:
            frame[col] = 0
    savings_cols = [c for c in frame if re.search(r'\(\s*saving\s*\)', c, re.I) and not re.search('actual', c, re.I)]
    numeric_cols = list(dict.fromkeys([SPEND, QTY, "Total Projected Saving"] + savings_cols))
    for col in numeric_cols:
        if col in frame:
            frame[col] = pd.to_numeric(frame[col].astype('string').str.replace(',', '', regex=False).str.replace('$', '', regex=False), errors='coerce').fillna(0.0)
    if "Total Projected Saving" in frame:
        # Match original JS: use this field whenever it exists, even if zero.
        frame["_savings_usd"] = frame["Total Projected Saving"]
    else:
        frame["_savings_usd"] = frame[savings_cols].sum(axis=1) if savings_cols else 0.0
    gate = frame["Stage Gate"].astype('string').fillna('') if "Stage Gate" in frame else pd.Series('', index=frame.index)
    frame["_status"] = np.where(gate.str.contains('4', regex=False), "Realized", "Pipeline")
    return frame


def money(x): return f"${x/1_000_000:,.2f} MUSD"
def style_fig(fig, height=330):
    fig.update_layout(height=height, margin=dict(l=10,r=12,t=28,b=18), paper_bgcolor='white', plot_bgcolor='white',
                      font=dict(family='Inter, sans-serif',color='#33415c',size=12),
                      legend=dict(orientation='h', y=1.15, x=0), hoverlabel=dict(bgcolor='white'))
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor='#edf0f7', zeroline=False)
    return fig


def plot_or_empty(fig, key):
    st.plotly_chart(style_fig(fig), use_container_width=True, config={'displaylogo':False}, key=key)


def reset_filters():
    for i in range(len(FILTERS)):
        st.session_state[f'f_{i}'] = []
    st.session_state['page'] = 1

with st.sidebar:
    st.markdown('<div class="brand"><span class="brand-icon">▥</span><div><div class="brand-name">Archroma Analytics</div><div class="brand-sub">Supply Chain Control Center</div></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-label">GLOBAL FILTERS</div>', unsafe_allow_html=True)
    st.button('↺ Reset Filters', on_click=reset_filters, use_container_width=True)

# Uploader is placed after the nine filters, as in the original Vercel sidebar.
# The upload widget must be instantiated before the dataset is loaded.
with st.sidebar:
    upload = st.file_uploader('Upload New Excel / CSV', type=['xlsx','xls','csv'], help='Uploaded files are processed in Streamlit server memory.')

try:
    payload = upload.getvalue() if upload else None
    df = load_dataset(payload, upload.name if upload else '')
except Exception as exc:
    st.error(f'Unable to read the file: {exc}. For .xls install xlrd; for .xlsx install openpyxl.')
    st.stop()

# Reset widgets when the uploaded dataset changes.
dataset_id = hashlib.sha256(payload).hexdigest() if payload is not None else 'sample'
if st.session_state.get('_dataset_id') != dataset_id:
    for i in range(len(FILTERS)):
        st.session_state[f'f_{i}'] = []
    st.session_state['_dataset_id'] = dataset_id
    st.session_state['page'] = 1

# Forward-only cascading options, with automatic invalid downstream selection cleanup.
filtered = df
with st.sidebar:
    for i, (label, col) in enumerate(FILTERS):
        key = f'f_{i}'
        choices = sorted(filtered[col].dropna().unique().tolist(), key=lambda x: x.casefold())
        current = st.session_state.get(key, [])
        valid = [v for v in current if v in choices]
        if current != valid:
            st.session_state[key] = valid
        selected = st.multiselect(f'{i+1}. {label}', options=choices, key=key, placeholder='All', help=f'Column: {col}')
        if selected:
            filtered = filtered.loc[filtered[col].isin(selected)]
    st.caption(f'{len(filtered):,} / {len(df):,} records matched')
    st.markdown('''<div class="nav-label">QUICK PAGE NAVIGATION</div>
    <a class="nav-item" href="#executive-kpi-summary">▥ &nbsp; Executive KPI Summary</a>
    <a class="nav-item" href="#analytics-overview">▤ &nbsp; Analytics Charts</a>
    <a class="nav-item" href="#savings-efficiency-roi-heatmap">◈ &nbsp; ROI Efficiency Heatmap</a>
    <a class="nav-item" href="#filtered-master-data-registry">▦ &nbsp; Data Registry Table</a>''',unsafe_allow_html=True)
    st.divider()
    st.markdown('<div class="nav-label">DATA MANAGEMENT</div>',unsafe_allow_html=True)
    upload_note = 'Sample dataset' if upload is None else upload.name
    st.caption(f'Current source: {upload_note}')
    st.divider()
    st.caption('🔒 Uploaded data stays in this Streamlit server process. Use localhost for fully local operation.')

st.markdown('''<div class="page-head"><div><h2>Procurement &amp; Supply Chain Performance</h2><p>Live analytical insights, savings tracking, and ROI risk monitoring.</p></div><span class="head-badge">SUPPLY CHAIN CONTROL CENTER</span></div>''', unsafe_allow_html=True)
if not len(filtered):
    st.warning('No records match the selected filters. Use Reset Filters to start over.')
    st.stop()

spend = float(filtered[SPEND].sum())
qty = float(filtered[QTY].sum())
savings = float(filtered['_savings_usd'].sum())
realized = float(filtered.loc[filtered['_status']=='Realized','_savings_usd'].sum())
pipeline = savings - realized

st.markdown('<div id="executive-kpi-summary" class="section-heading">EXECUTIVE KPI SUMMARY</div>',unsafe_allow_html=True)
cols = st.columns(4)
with cols[0]: st.metric('Total YTD Spend', money(spend))
with cols[1]: st.metric('Total PO Quantity', f'{qty:,.0f} Kgs')
with cols[2]:
    st.metric('Projected Savings', money(savings))
    st.caption(f'Realized: ${realized/1e6:,.2f}M · Pipeline: ${pipeline/1e6:,.2f}M')
with cols[3]: st.metric('Active Line Items', f'{len(filtered):,}')

with st.expander('🔎 KPI drill-downs and detailed records', expanded=False):
    metric = st.selectbox('Metric to inspect', ['Spend', 'PO Quantity', 'Projected Savings', 'Active Line Items'], key='kpi_choice')
    group = st.selectbox('Break down by', ['Plant Region', 'Sub Category', 'Initiative Type', 'Catergory Manager', 'Plant'], key='kpi_group')
    field = {'Spend':SPEND,'PO Quantity':QTY,'Projected Savings':'_savings_usd','Active Line Items':None}[metric]
    if field:
        summary = filtered.groupby(group,dropna=False,observed=True)[field].agg(['sum','count']).reset_index().sort_values('sum',ascending=False)
    else:
        summary = filtered.groupby(group,dropna=False,observed=True).size().reset_index(name='count').sort_values('count',ascending=False)
    st.dataframe(summary, hide_index=True, use_container_width=True)
    if metric == 'Projected Savings':
        st.dataframe(filtered.groupby(['_status',group],observed=True)['_savings_usd'].sum().reset_index(), hide_index=True, use_container_width=True)

# Automated, deterministic local insights (no remote AI calls).
regional = filtered.groupby('Plant Region',observed=True)[SPEND].sum().sort_values(ascending=False)
if spend > 0 and len(regional):
    biggest = regional.index[0]
    st.markdown(f'<div class="insight"><b>◈ AUTOMATED RISK &amp; EFFICIENCY SCANNER</b><br><br>{html.escape(str(biggest))} represents {regional.iloc[0]/spend:.1%} of filtered spend. Projected savings / spend: {savings/spend:.1%}. {(filtered["_status"]=="Pipeline").sum():,} line items remain in pipeline.</div>',unsafe_allow_html=True)

st.markdown('<div id="analytics-overview" class="section-heading">ANALYTICS CHARTS</div>',unsafe_allow_html=True)
left, right = st.columns(2, gap='medium')
with left:
    with st.container(border=True):
        st.markdown('**Spend by Sub Category**')
        agg = filtered.groupby('Sub Category',observed=True)[SPEND].sum().sort_values(ascending=False).reset_index()
        agg['Spend (MUSD)'] = agg[SPEND]/1e6
        fig = px.bar(agg, x='Sub Category', y='Spend (MUSD)', color_discrete_sequence=['#5953d8'])
        fig.update_xaxes(tickangle=-25)
        plot_or_empty(fig,'subcat_chart')
with right:
    with st.container(border=True):
        st.markdown('**Global Geographical Regional Spend**')
        r = filtered.groupby('Plant Region',observed=True)[SPEND].agg(['sum','count']).reset_index()
        r[['lat','lon']] = pd.DataFrame([REGION_COORDS.get(str(x),(0,0)) for x in r['Plant Region']], index=r.index)
        r['MUSD'] = r['sum']/1e6
        fig = px.scatter_geo(r, lat='lat',lon='lon',size='sum',hover_name='Plant Region',hover_data={'MUSD':':.2f','count':True,'lat':False,'lon':False,'sum':False},
                             projection='natural earth', color='MUSD', color_continuous_scale='Purples', size_max=32)
        fig.update_geos(showcoastlines=True, coastlinecolor='#aab3c4', showland=True,landcolor='#edf0f8',
                        showcountries=True,countrycolor='#cbd2df',showocean=True,oceancolor='#f9faff',bgcolor='white')
        fig.update_layout(coloraxis_showscale=False)
        plot_or_empty(fig,'regional_map')
        st.caption('Region markers are representative locations, not precise plant coordinates.')
left, right = st.columns(2, gap='medium')
with left:
    with st.container(border=True):
        st.markdown('**Top 5 Materials by Spend**')
        top = filtered.groupby('Material Name',observed=True)[SPEND].sum().nlargest(5).sort_values().reset_index()
        top['Spend (MUSD)'] = top[SPEND]/1e6
        fig = px.bar(top,x='Spend (MUSD)',y='Material Name',orientation='h',color_discrete_sequence=['#7771e8'])
        plot_or_empty(fig,'top_materials')
with right:
    with st.container(border=True):
        st.markdown('**Monthly Savings & Volume Trend · Oct 2026–Sep 2027**')
        trend = []
        for m in MONTHS:
            month, year = m.split()
            prefix = f'{month.lower()} {year}'
            sav_cols = [c for c in filtered if prefix in c.lower() and '(saving)' in c.lower()]
            vol_cols = [c for c in filtered if prefix in c.lower() and '(vol)' in c.lower()]
            sav = sum(pd.to_numeric(filtered[c],errors='coerce').fillna(0).sum() for c in sav_cols)
            vol = sum(pd.to_numeric(filtered[c],errors='coerce').fillna(0).sum() for c in vol_cols)
            trend.append((m,sav,vol))
        t = pd.DataFrame(trend,columns=['Month','Savings USD','Volume Kgs'])
        fig = make_subplots(specs=[[{'secondary_y':True}]])
        fig.add_trace(go.Bar(x=t.Month,y=t['Savings USD']/1e6,name='Savings (MUSD)',marker_color='#10b981'),secondary_y=False)
        fig.add_trace(go.Scatter(x=t.Month,y=t['Volume Kgs'],name='Volume (Kgs)',mode='lines+markers',line=dict(color='#6256d9',width=3)),secondary_y=True)
        fig.update_yaxes(title_text='Savings (MUSD)',secondary_y=False)
        fig.update_yaxes(title_text='Volume (Kgs)',secondary_y=True,showgrid=False)
        plot_or_empty(fig,'monthly_trend')

st.markdown('<div id="savings-efficiency-roi-heatmap" class="section-heading">🔥 Savings Efficiency & ROI Heatmap</div>',unsafe_allow_html=True)
st.caption('Rows: Initiative Types ranked by total savings (USD). Columns: Sub Categories. Purple = spend (MUSD); green = savings percentage and amount (MUSD).')
heat = filtered.groupby(['Initiative Type','Sub Category'],observed=True).agg(spend=(SPEND,'sum'),savings=('_savings_usd','sum'),items=(SPEND,'size')).reset_index()
row_order = heat.groupby('Initiative Type')['savings'].sum().sort_values(ascending=False).index.tolist()
col_order = sorted(heat['Sub Category'].unique().tolist())
max_spend = max(float(heat.spend.max()),1)
heat['pct'] = np.where(heat.spend>0,heat.savings/heat.spend*100,0)
max_pct = max(float(heat.pct.clip(lower=0).max()),0.001)
cell_lookup = {(r['Initiative Type'],r['Sub Category']):r for _,r in heat.iterrows()}

# HTML table provides true split-box heatmap cells without a heavy Plotly trace per cell.
# Escaping all labels avoids HTML injection from user-uploaded spreadsheets.
parts = ['<div style="overflow-x:auto;background:white;border:1px solid #e5eaf3;border-radius:14px;padding:12px">',
         '<table style="border-collapse:separate;border-spacing:3px;width:100%;font-size:12px"><thead><tr>',
         '<th style="text-align:left;min-width:195px;padding:9px">Initiative / Sub Category</th>']
for cat in col_order:
    parts.append(f'<th style="min-width:165px;padding:9px;text-align:center;color:#26335b">{html.escape(str(cat))}</th>')
parts.append('</tr></thead><tbody>')
for init in row_order:
    row = heat.loc[heat['Initiative Type']==init]
    total_s = row.savings.sum(); total_p = row.spend.sum()
    parts.append(f'<tr><th style="text-align:left;background:#f4f5fc;border-radius:7px;padding:9px">{html.escape(str(init))}'
                 f'<div style="font-size:10px;color:#6256d9">${total_p/1e6:.2f}M spend · ${total_s/1e6:.2f}M savings</div></th>')
    for cat in col_order:
        r = cell_lookup.get((init,cat))
        if r is None:
            parts.append('<td style="text-align:center;background:#f8f9fc;color:#a6acbc;border-radius:7px">—</td>')
            continue
        intensity = min(max(float(r.spend)/max_spend,.12),1)
        green = min(max(max(float(r.pct),0)/max_pct,.15),1)
        a = .13+.75*intensity; b=.13+.75*green
        parts.append(f'<td title="{int(r["items"])} records" style="padding:2px"><div style="display:flex;gap:2px;text-align:center;font-weight:650">'
                     f'<div style="flex:1;background:rgba(126,58,210,{a:.2f});color:{"white" if a>.55 else "#222"};padding:12px 3px;border-radius:6px">'
                     f'Spend<br>${r.spend/1e6:.2f}M</div>'
                     f'<div style="flex:1;background:rgba(16,185,129,{b:.2f});color:{"white" if b>.55 else "#222"};padding:12px 3px;border-radius:6px">'
                     f'{r.pct:.1f}%<br>${r.savings/1e6:.2f}M</div></div></td>')
    parts.append('</tr>')
parts.append('</tbody></table></div>')
st.markdown(''.join(parts),unsafe_allow_html=True)
with st.expander('Heatmap detailed breakdown'):
    st.dataframe(heat.sort_values(['savings'],ascending=False),hide_index=True,use_container_width=True)

st.markdown('<div id="filtered-master-data-registry" class="section-heading">Filtered Master Data Registry</div>',unsafe_allow_html=True)
search = st.text_input('Search all columns',placeholder='Type a material, supplier, plant, manager, code…',key='table_search')
registry = filtered.drop(columns=['_savings_usd','_status'],errors='ignore')
if search.strip():
    term = search.strip()
    # Vectorized across columns; avoids building a single giant joined string per row.
    mask = pd.Series(False,index=registry.index)
    for col in registry.columns:
        mask |= registry[col].astype('string').str.contains(term,case=False,regex=False,na=False)
    registry = registry.loc[mask]

ctrl1,ctrl2,ctrl3 = st.columns([1,1,2])
with ctrl1: page_size = st.selectbox('Rows per page',[25,50,100],index=0)
num_pages = max(1,math.ceil(len(registry)/page_size))
if st.session_state.get('page',1)>num_pages:
    st.session_state['page']=num_pages
with ctrl2: page = st.number_input('Page',min_value=1,max_value=num_pages,step=1,key='page')
with ctrl3:
    st.caption(f'{len(registry):,} matching rows · page {page:,} of {num_pages:,}')
    st.download_button('⬇ Download Filtered Data (CSV)', data=registry.to_csv(index=False).encode('utf-8-sig'),
                       file_name='procurement_filtered_data.csv',mime='text/csv',use_container_width=True)
start=(page-1)*page_size
st.dataframe(registry.iloc[start:start+page_size],hide_index=True,use_container_width=True,height=460)
st.caption('Data is processed with Pandas in memory. No external analytics, fonts, map tiles, or API requests are required for processing; the app does not request third-party APIs or hosted assets.')
