"""NASA C-MAPSS Turbofan Health & Degradation Telemetry Dashboard (Streamlit + Plotly)."""
import streamlit as st, pandas as pd, plotly.graph_objects as go, plotly.express as px, joblib
from pathlib import Path

st.set_page_config(page_title="AERO-CMAPSS // Turbofan Telemetry", page_icon="✈️",
                   layout="wide", initial_sidebar_state="expanded")

G, A, R = "#5F8F76", "#B7965A", "#B86C74"
PURPLE, TEAL = "#857B8F", "#658E89"
TEXT, MUT, BG, PANEL, GRID = "#35443A", "#778276", "#EEF2EA", "#F8FAF5", "#DCE4D8"

# ---------------- CSS ----------------
CSS = """<style>
:root{--ink:#35443a;--muted:#778276;--line:#dce4d8}
.stApp{background:linear-gradient(135deg,#edf2e9 0%,#f4f4ec 55%,#eaf1ed 100%);color:var(--ink);font-family:'Times New Roman',Georgia,serif}
.stApp [data-testid="stMarkdownContainer"],.stApp label,.stApp p,.stApp h1,.stApp h2,.stApp h3{color:var(--ink)}
header[data-testid="stHeader"]{background:rgba(242,246,238,.92);backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#f3f6ef 0%,#eaf0e8 100%);border-right:1px solid #dce4d8}
.telemetry-card{background:linear-gradient(145deg,#f9fbf6 0%,#f0f4ec 100%);border:1px solid #dce5d8;border-radius:18px;padding:14px 18px;margin-bottom:12px;box-shadow:0 8px 24px rgba(66,91,70,.08)}
.metric-label{font-size:11px;text-transform:uppercase;letter-spacing:.09em;color:#6d7c6f;margin-bottom:5px;font-weight:700}
.metric-value{font-size:25px;font-weight:700;color:var(--ink);font-family:'Times New Roman',Georgia,serif;letter-spacing:-.02em}
.metric-sub{font-size:12px;color:#778276;margin-top:3px}
.stTabs [data-baseweb="tab-list"]{gap:8px;background:rgba(247,249,243,.9);padding:6px;border-radius:14px;border:1px solid #dce4d8;box-shadow:0 6px 18px rgba(66,91,70,.06)}
.stTabs [data-baseweb="tab"]{border-radius:10px;color:#778276;padding:8px 16px;font-weight:700;font-size:13px;border:none!important;background:transparent}
.stTabs [aria-selected="true"]{background:linear-gradient(120deg,#e1eadf 0%,#e7eee4 100%)!important;color:#35443a!important;box-shadow:inset 0 0 0 1px rgba(95,143,118,.2)}
.stButton>button{border:1px solid #d1ddcf;border-radius:10px;background:linear-gradient(120deg,#f4f7ef,#eaf1e9);color:#405746;font-family:'Times New Roman',Georgia,serif;font-weight:600;transition:all .18s ease}
.stButton>button:hover{border-color:#9bb49d;color:#35443a;box-shadow:0 4px 12px rgba(66,91,70,.12)}
.stSelectbox [data-baseweb="select"]>div,.stRadio [data-baseweb="radio"]{border-color:#d5dfd3}
.aero-table-container{border:1px solid #dce4d8;border-radius:14px;overflow:hidden;background:linear-gradient(135deg,#f9fbf6 0%,#f1f5ee 100%);margin:12px 0 20px 0;box-shadow:0 8px 20px rgba(66,91,70,.06)}
table.aero-table{width:100%;border-collapse:collapse;font-size:13px;color:var(--ink);text-align:left;font-family:'Times New Roman',Georgia,serif}
table.aero-table th{background:linear-gradient(110deg,#e8eee4 0%,#e4ece5 100%);color:#586b5b;padding:12px 16px;font-size:11px;text-transform:uppercase;letter-spacing:.08em;font-weight:700;border-bottom:1px solid #dce4d8}
table.aero-table td{padding:11px 16px;border-bottom:1px solid #e7ece3;color:var(--ink)}
table.aero-table tr:hover{background:#edf3e9}
table.aero-table tr:last-child td{border-bottom:none}
.num-cell{font-family:'Times New Roman',Georgia,serif;font-variant-numeric:tabular-nums;text-align:right}
.text-center{text-align:center}
.badge-good{background:#e4eee2;color:#426b4e;border:1px solid #cbdcc8;padding:4px 9px;border-radius:999px;font-size:10px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;display:inline-block}
.badge-mid{background:#f1eddf;color:#826b3f;border:1px solid #e2d9bd;padding:4px 9px;border-radius:999px;font-size:10px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;display:inline-block}
.badge-bad{background:#f2e5e3;color:#98565b;border:1px solid #e3cfcd;padding:4px 9px;border-radius:999px;font-size:10px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;display:inline-block}
.status-banner-good{background:linear-gradient(105deg,#e4eee2 0%,#f5f7f1 100%);border:1px solid #d7e2d4;border-left:4px solid #5f8f76;border-radius:13px;padding:12px 18px;box-shadow:0 8px 20px rgba(67,110,78,.08)}
.status-banner-mid{background:linear-gradient(105deg,#f1eddf 0%,#f6f6ef 100%);border:1px solid #e5dfcf;border-left:4px solid #b7965a;border-radius:13px;padding:12px 18px;box-shadow:0 8px 20px rgba(146,119,67,.08)}
.status-banner-bad{background:linear-gradient(105deg,#f2e5e3 0%,#f7f4ef 100%);border:1px solid #e7d8d5;border-left:4px solid #b86c74;border-radius:13px;padding:12px 18px;box-shadow:0 8px 20px rgba(148,85,91,.08)}
[style*="color: #f9fafb"],[style*="color:#f9fafb"],[style*="color: #f3f4f6"],[style*="color:#f3f4f6"],[style*="color: #e5e7eb"],[style*="color:#e5e7eb"],[style*="color: #ffffff"],[style*="color:#ffffff"]{color:var(--ink)!important}
[style*="color: #9ca3af"],[style*="color:#9ca3af"],[style*="color: #6b7280"],[style*="color:#6b7280"]{color:var(--muted)!important}
"""
st.markdown(CSS + "</style>", unsafe_allow_html=True)


# ---------------- data ----------------
def resolve_run_dirs():
    here = Path(__file__).resolve().parent
    for base in (here, here / "data preprocessing", Path.cwd(), Path.cwd() / "data preprocessing"):
        for root in (base / "data preprocessing" / "processed_output", base / "processed_output"):
            runs = sorted((p for p in root.glob("run_*") if p.is_dir()), key=lambda p: p.name) if root.is_dir() else []
            if runs:
                return runs[-1], (runs[-2] if len(runs) > 1 else None)
    raise FileNotFoundError("No run_* folders found. Run the preprocessing pipeline first.")

V2_RUN_DIR, V1_RUN_DIR = resolve_run_dirs()


@st.cache_data(show_spinner=False)
def load_data():
    rd = lambda d: pd.read_csv(d / "results" / "results.csv").sort_values("macroF1", ascending=False)
    v1 = rd(V1_RUN_DIR) if V1_RUN_DIR is not None and (V1_RUN_DIR / "results" / "results.csv").exists() else None
    cols = ['unit', 'subset', 'cycle', 'rul', 'label', 's2', 's3', 's4', 's7', 's8', 's9', 's11', 's12', 's15', 's20', 's21']
    test_df = pd.read_csv(V2_RUN_DIR / "test_all.csv", usecols=cols)
    u, s = (joblib.load(V2_RUN_DIR / "results" / f) for f in ("unsup.pkl", "sup.pkl"))
    return (rd(V2_RUN_DIR), v1, test_df,
            {**u.get("PRED", {}), **s.get("PRED", {})}, {**u.get("SCORE", {}), **s.get("SCORE", {})})

v2_results, v1_results, test_df, all_preds, all_scores = load_data()


# ---------------- helpers ----------------
STATUS = {
    "normal": ("GOOD // NORMAL", "good", G, "Healthy nominal operation. No degradation detected (RUL > 60 cycles)."),
    "near_anomaly": ("MID // NEAR ANOMALY", "mid", A, "Incipient degradation detected. Advisory alert window active (15 < RUL ≤ 60)."),
    "anomaly": ("BAD // ANOMALY", "bad", R, "Critical degradation threshold breached. Immediate overhaul required (RUL ≤ 15)."),
}
LABEL_NUM = {"normal": 0, "near_anomaly": 1, "anomaly": 2}


def status(label):
    n, k, c, d = STATUS.get(label, STATUS["anomaly"])
    return dict(name=n, banner=f"status-banner-{k}", color=c, desc=d)


def apply_persistence(preds, k=3):
    inv = list(LABEL_NUM)
    s = pd.Series([LABEL_NUM.get(p, 0) for p in preds]).rolling(k, min_periods=1).min().astype(int)
    return [inv[v] for v in s]


def card(label, value, sub, color=None, unit="", unit_px=14, tint_label=False):
    border = f"border-left:3px solid {color};" if color else ""
    lc = f"color:{color};" if color and tint_label else ""
    vc = f"color:{color};" if color else ""
    u = f' <span style="font-size:{unit_px}px;font-weight:500;color:{MUT};">{unit}</span>' if unit else ""
    st.markdown(f'<div class="telemetry-card" style="{border}"><div class="metric-label" style="{lc}">{label}</div>'
                f'<div class="metric-value" style="{vc}">{value}{u}</div><div class="metric-sub">{sub}</div></div>',
                unsafe_allow_html=True)


def banner(i, label, sub, flex=False):
    fl = "display:flex;justify-content:space-between;" if flex else ""
    st.markdown(f'<div class="{i["banner"]}"><div class="metric-label" style="{fl}color:{i["color"]};">{label}</div>'
                f'<div style="font-size:16px;font-weight:800;color:{TEXT};margin-top:2px;">{i["name"]}</div>'
                f'<div style="font-size:11px;color:{MUT};margin-top:4px;">{sub}</div></div>', unsafe_allow_html=True)


def td(v, color=TEXT, bold=False, cls="num-cell"):
    return f'<td class="{cls}" style="color:{color};{"font-weight:700;" if bold else ""}">{v}</td>'


def table(heads, rows):
    h = "".join(f'<th style="width:{w}%;" class="{c}">{t}</th>' for t, w, c in heads)
    b = "".join("<tr>" + "".join(r) + "</tr>" for r in rows)
    st.markdown(f'<div class="aero-table-container"><table class="aero-table"><thead><tr>{h}</tr></thead>'
                f'<tbody>{b}</tbody></table></div>', unsafe_allow_html=True)


def dark(fig, h, title=None, xt=None, yt=None, margin=None, **kw):
    fig.update_layout(paper_bgcolor=BG, plot_bgcolor=PANEL, height=h, font=dict(family="Times New Roman, Georgia, serif", color=TEXT),
                      margin=margin or dict(l=40, r=20, t=44, b=34), **kw)
    if title:
        fig.update_layout(title=dict(text=title, font=dict(size=15, color=TEXT)))
    tf = dict(color=MUT, size=11)
    fig.update_xaxes(gridcolor=GRID, tickfont=dict(color=MUT), title_text=xt, title_font=tf)
    fig.update_yaxes(gridcolor=GRID, tickfont=dict(color=MUT), title_text=yt, title_font=tf)
    return fig


def section(title, sub):
    st.markdown(f'<div style="margin-bottom:14px;"><span style="font-weight:700;font-size:15px;color:{TEXT};">{title}</span>'
                f'<span style="color:{MUT};font-size:13px;margin-left:8px;">{sub}</span></div>', unsafe_allow_html=True)


def dcol(v, up_good=True):
    v = v if up_good else -v
    return G if v > 0 else (R if v < -0.01 else MUT)

sg = lambda v: "+" if v > 0 else ""
SUP = ["MLP", "Random Forest", "Gradient Boosting", "Logistic Regression", "Majority/Random (floor)"]


# ---------------- header + fleet metrics ----------------
st.markdown(f"""<div style="display:flex;justify-content:space-between;align-items:flex-end;padding:6px 0 16px 0;border-bottom:1px solid #dce4d8;margin-bottom:20px;">
<div><div style="font-size:11px;text-transform:uppercase;letter-spacing:.12em;color:{MUT};font-weight:700;">NASA C-MAPSS // Turbofan Degradation &amp; Fault Diagnostics</div>
<div style="font-size:28px;font-weight:800;color:{TEXT};letter-spacing:-.035em;margin-top:4px;">Turbofan Fleet Health &amp; Early Warning Telemetry</div></div>
<div style="text-align:right;display:flex;gap:8px;"><span class="badge-good">RUN: V2 (28 FEATS)</span><span class="badge-mid">3-CLASS HEALTH STATES</span><span class="badge-bad">CANARI + PERSISTENCE</span></div></div>""",
            unsafe_allow_html=True)

n_all, counts = len(test_df), test_df["label"].value_counts()
c1, c2, c3, c4, c5 = st.columns(5)
with c1: card("Monitored Fleet", test_df["unit"].nunique(), "Subsets FD001 – FD004", unit="units")
with c2: card("Total Test Cycles", f"{n_all:,}", "Continuous mission data", unit="cycles")
for col, key, lbl, color, sub in [(c3, "normal", "Good // Normal", G, "nominal flight duration"),
                                  (c4, "near_anomaly", "Mid // Near Anomaly", A, "advisory warning window"),
                                  (c5, "anomaly", "Bad // Anomaly", R, "critical failure window")]:
    with col:
        card(lbl, f"{counts[key]:,}", f"{counts[key] / n_all * 100:.1f}% {sub}", color, tint_label=True)

tab1, tab2, tab3, tab4 = st.tabs(["ENGINE TELEMETRY INSPECTOR", "MODEL BENCHMARK MATRIX",
                                  "V1 VS V2 FEATURE IMPACT", "PERSISTENCE & THRESHOLD LAB"])

# ================= TAB 1: ENGINE INSPECTOR =================
with tab1:
    section("Interactive Engine Degradation & Telemetry Viewer",
            "Scrub through operating cycles, inspect sensor drift, and compare ground truth vs AI prediction.")
    c_sub, c_eng, c_mod, c_pers = st.columns([1.2, 1.5, 1.8, 1.2])
    with c_sub:
        subset_choice = st.selectbox("Fleet Subset", ["ALL", "FD001", "FD002", "FD003", "FD004"], index=1,
                                     help="FD001: 1 condition, HPC fault | FD002: 6 conditions | FD003: 1 cond, HPC+Fan | FD004: 6 cond, HPC+Fan")
    units = test_df["unit"] if subset_choice == "ALL" else test_df.loc[test_df["subset"] == subset_choice, "unit"]
    with c_eng:
        selected_unit = st.selectbox("Engine Unit", sorted(units.unique()), index=0)
    with c_mod:
        names = list(all_preds)
        selected_model = st.selectbox("Diagnostic Model", names, index=names.index("CANARI") if "CANARI" in names else 0)
    with c_pers:
        k = st.selectbox("Persistence Filter (K)", [1, 3, 5, 8], index=1,
                         help="K consecutive cycles required before raising alert level")

    eng = test_df[test_df["unit"] == selected_unit].sort_values("cycle")
    idx, eng_df = eng.index.tolist(), eng.reset_index(drop=True)
    raw_pred = [all_preds[selected_model][i] for i in idx]
    active = apply_persistence(raw_pred, k) if k > 1 else raw_pred
    scores = [all_scores[selected_model][i] for i in idx] if selected_model in all_scores else None

    total = len(eng_df)
    cycles = eng_df["cycle"].tolist()
    first_warn = next((c for c, p in zip(cycles, active) if p in ("near_anomaly", "anomaly")), None)
    lead = int(eng_df["rul"].iloc[cycles.index(first_warn)]) if first_warn else 0

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    col_scrub, col_quick = st.columns([3.5, 1.5])
    with col_scrub:
        cur = st.slider("Cycle Telemetry Scrubber", 1, total, min(total, 30), step=1)
    with col_quick:
        q_start = st.button("Start (C=1)")
        q_warn = st.button(f"First Warn (C={first_warn or 'N/A'})")
        q_end = st.button(f"End (C={total})")
    if q_start: cur = 1
    elif q_warn and first_warn: cur = first_warn
    elif q_end: cur = total

    row = eng_df[eng_df["cycle"] == cur].iloc[0]
    gt, pr, rul = row["label"], active[cur - 1], row["rul"]
    gi, pi = status(gt), status(pr)
    match, mcol = ("✓ MATCH", G) if gt == pr else ("⚠ DEVIATION", A)

    st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
    l1, l2, l3, l4 = st.columns(4)
    with l1: banner(gi, f"Ground Truth (Cycle {cur})", gi["desc"])
    with l2: banner(pi, f'<span>Model Output: {selected_model}</span><span style="color:{mcol};font-weight:700;">{match}</span>',
                    f"Filter: K={k} consecutive cycles", flex=True)
    with l3:
        card("Remaining Useful Life (RUL)", rul, f"Progress: {cur} / {total} cycles completed",
             G if rul > 60 else (A if rul > 15 else R), "cycles", 13)
    with l4:
        card("Alarm Lead Time", lead, f"First advisory alarm at Cycle {first_warn or 'None'}",
             G if lead >= 40 else (A if lead > 15 else R), "cycles", 13)

    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
    p1, p2 = st.columns([1.6, 1.4])
    ZC = {0: G, 1: A, 2: R}

    with p1:
        pnum = [LABEL_NUM[x] for x in active]
        f = go.Figure()
        for y0, y1, c in [(-0.4, 0.5, "95,143,118"), (0.5, 1.5, "183,150,90"), (1.5, 2.4, "184,108,116")]:
            f.add_hrect(y0=y0, y1=y1, fillcolor=f"rgba({c},0.10)", line_width=0)
        f.add_trace(go.Scatter(x=eng_df["cycle"], y=[LABEL_NUM[x] for x in eng_df["label"]], mode="lines",
                               name="Ground Truth", line=dict(color=MUT, width=2, dash="dot")))
        f.add_trace(go.Scatter(x=eng_df["cycle"], y=pnum, mode="lines+markers", name=f"Predicted ({selected_model})",
                               line=dict(color=PURPLE, width=2), marker=dict(size=5, color=[ZC[p] for p in pnum])))
        f.add_vline(x=cur, line_width=2, line_dash="dash", line_color=TEXT)
        dark(f, 280, f"Engine {selected_unit} // Health State Trajectory", xt="Operating Cycle",
             legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color=MUT, size=10)))
        f.update_yaxes(tickvals=[0, 1, 2], ticktext=["GOOD (Normal)", "MID (Near Anomaly)", "BAD (Anomaly)"],
                       tickfont=dict(color=MUT, size=11), range=[-0.3, 2.3])
        st.plotly_chart(f, width="stretch")

    with p2:
        f = go.Figure()
        if scores is not None:
            f.add_trace(go.Scatter(x=eng_df["cycle"], y=scores, mode="lines", name="Anomaly Score", line=dict(color=A, width=2.5)))
            yt = "Raw Anomaly Score"
        else:
            f.add_trace(go.Scatter(x=eng_df["cycle"], y=eng_df["rul"], mode="lines", name="Remaining Useful Life (RUL)",
                                   line=dict(color=G, width=2.5)))
            yt = "RUL (Cycles)"
        f.add_vline(x=cur, line_width=2, line_dash="dash", line_color=TEXT)
        dark(f, 280, f"Engine {selected_unit} // Degradation Metric", xt="Operating Cycle", yt=yt,
             legend=dict(font=dict(color=MUT, size=10), yanchor="top", y=0.98, xanchor="left", x=0.02))
        st.plotly_chart(f, width="stretch")

    st.markdown(f"<div style='font-size:13px;font-weight:700;color:{TEXT};margin:12px 0 6px 0;'>SENSOR TELEMETRY CHANNELS (NORMALIZED SENSORS S2, S4, S11, S12, S15)</div>",
                unsafe_allow_html=True)
    SENS = {"s2": (G, "s2 (LPC Outlet Temp)"), "s4": (A, "s4 (LPT Outlet Temp)"),
            "s11": (R, "s11 (Static HPC Pressure)"), "s12": (PURPLE, "s12 (Physical Fan Speed)"),
            "s15": (TEAL, "s15 (Bypass Ratio)")}
    f = go.Figure()
    for s, (c, nm) in SENS.items():
        f.add_trace(go.Scatter(x=eng_df["cycle"], y=eng_df[s], mode="lines", name=nm, line=dict(color=c, width=1.8)))
    f.add_vline(x=cur, line_width=2, line_dash="dash", line_color=TEXT)
    dark(f, 260, xt="Operating Cycle", yt="Z-Normalized Sensor Reading", margin=dict(l=40, r=20, t=20, b=30),
         legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(color=MUT, size=10)))
    st.plotly_chart(f, width="stretch")

# ================= TAB 2: BENCHMARK =================
with tab2:
    section("Model Benchmark & Performance Matrix", "Evaluation across all 13 models on 49,041 test engine cycles.")
    cf, cs = st.columns([2, 1])
    with cf:
        paradigm = st.radio("Filter Paradigm", ["All Models (13)", "Supervised Classifiers", "Unsupervised Anomaly Detectors"], horizontal=True)
    with cs:
        sort_by = st.selectbox("Sort Table By", ["macroF1", "near_F1", "FAR", "ROC_AUC", "PR_AUC"], index=0)

    d = v2_results.copy()
    if paradigm == "Supervised Classifiers": d = d[d["model"].isin(SUP)]
    elif paradigm == "Unsupervised Anomaly Detectors": d = d[~d["model"].isin(SUP)]
    d = d.sort_values(sort_by, ascending=(sort_by == "FAR"))

    rows = []
    for _, r in d.iterrows():
        badge = '<span class="badge-good">SUPERVISED</span>' if r["model"] in SUP else '<span class="badge-mid">UNSUPERVISED</span>'
        f1c = G if r["macroF1"] >= 0.80 else (A if r["macroF1"] >= 0.60 else R)
        fac = G if r["FAR"] <= 0.08 else (A if r["FAR"] <= 0.15 else R)
        rows.append([td(r["model"], TEXT, True, ""), f'<td class="text-center">{badge}</td>',
                     td(f'{r["macroF1"]:.3f}', f1c, True), td(f'{r["near_F1"]:.3f}'),
                     td(f'{r["near_P"]:.3f}', MUT), td(f'{r["near_R"]:.3f}', MUT),
                     td(f'{r["FAR"]:.3f}', fac, True), td(f'{r["PR_AUC"]:.3f}'), td(f'{r["ROC_AUC"]:.3f}')])
    table([("Model Architecture", 22, ""), ("Paradigm", 14, "text-center"), ("Macro F1", 9, "num-cell"),
           ("Near F1", 9, "num-cell"), ("Near Prec", 8, "num-cell"), ("Near Rec", 8, "num-cell"),
           ("False Alarm (FAR)", 10, "num-cell"), ("PR-AUC", 10, "num-cell"), ("ROC-AUC", 10, "num-cell")], rows)

    b1, b2 = st.columns(2)
    scale = [[0, R], [0.65, A], [1, G]]
    with b1:
        f = px.bar(v2_results.sort_values("macroF1"), x="macroF1", y="model", orientation="h", color="macroF1",
                   color_continuous_scale=scale, title="Macro-F1 Ranking (All Models)")
        dark(f, 360, margin=dict(l=140, r=20, t=40, b=40), coloraxis_showscale=False)
        f.update_xaxes(title_text="Macro F1"); f.update_yaxes(title_text="", tickfont=dict(color=TEXT))
        st.plotly_chart(f, width="stretch")
    with b2:
        f = px.scatter(v2_results, x="FAR", y="macroF1", text="model", color="near_F1", color_continuous_scale=scale,
                       title="Trade-off: Macro-F1 vs False Alarm Rate (FAR on Normal Rows)")
        f.update_traces(textposition="top right", marker=dict(size=11))
        dark(f, 360, xt="False Alarm Rate (Lower is Better)", yt="Macro F1 (Higher is Better)",
             margin=dict(l=40, r=40, t=40, b=40), coloraxis_colorbar=dict(title="Near F1", tickfont=dict(color=MUT)))
        st.plotly_chart(f, width="stretch")

# ================= TAB 3: V1 vs V2 =================
with tab3:
    section("Feature Engineering Impact: v1 (14 Raw Sensors) vs v2 (28 Sensors + Rolling Means)",
            "Direct empirical delta across feature sets.")
    if v1_results is not None:
        cols = ["model", "macroF1", "near_F1", "FAR"]
        m = v1_results[cols].merge(v2_results[cols], on="model", suffixes=("_v1", "_v2"))
        m["d_f1"], m["d_near"], m["d_far"] = (m["macroF1_v2"] - m["macroF1_v1"], m["near_F1_v2"] - m["near_F1_v1"],
                                              m["FAR_v2"] - m["FAR_v1"])
        m = m.sort_values("d_f1", ascending=False)
        rows = [[td(r["model"], TEXT, True, ""),
                 td(f'{r["macroF1_v1"]:.3f}', MUT), td(f'{r["macroF1_v2"]:.3f}', TEXT, True),
                 td(f'{sg(r["d_f1"])}{r["d_f1"]:.3f}', dcol(r["d_f1"]), True),
                 td(f'{r["near_F1_v1"]:.3f}', MUT), td(f'{r["near_F1_v2"]:.3f}', TEXT),
                 td(f'{sg(r["d_near"])}{r["d_near"]:.3f}', dcol(r["d_near"]), True),
                 td(f'{sg(r["d_far"])}{r["d_far"]:.3f}', dcol(r["d_far"], False), True)] for _, r in m.iterrows()]
        table([("Model Architecture", 25, ""), ("v1 Macro-F1 (14f)", 12, "num-cell"), ("v2 Macro-F1 (28f)", 12, "num-cell"),
               ("Δ Macro-F1", 13, "num-cell"), ("v1 Near-F1", 12, "num-cell"), ("v2 Near-F1", 12, "num-cell"),
               ("Δ Near-F1", 14, "num-cell"), ("Δ False Alarm", 14, "num-cell")], rows)

        f = go.Figure(go.Bar(name="Δ Macro F1", x=m["model"], y=m["d_f1"],
                             marker_color=[G if v >= 0 else R for v in m["d_f1"]]))
        dark(f, 300, "Net Macro-F1 Gain/Loss from 14 Rolling Means (v2 vs v1)", yt="Delta Macro F1",
             margin=dict(l=40, r=20, t=40, b=80))
        f.update_xaxes(tickangle=-30)
        st.plotly_chart(f, width="stretch")

# ================= TAB 4: PERSISTENCE LAB =================
with tab4:
    section("Persistence Filter & Threshold Optimization Lab",
            "Explore how consecutive alarm rules suppress transient false positives while maintaining early warning lead time.")
    t1, t2 = st.columns(2)
    title = lambda t: f'<div style="font-weight:700;font-size:14px;color:{TEXT};margin-bottom:8px;">{t}</div>'
    body = f'<div style="font-size:13px;color:{MUT};line-height:1.5;">'
    with t1:
        st.markdown(f'<div class="telemetry-card">{title("Consecutive Alarm Rule: K Cycles")}{body}'
                    f'In industrial gas turbines, sensor spikes can trigger transient alarms during nominal operation. A rolling persistence '
                    f'filter requires that an engine must generate <span style="color:{A};font-weight:700;">K consecutive alarms</span> before the '
                    f'operational state transitions from <span style="color:{G};">GOOD</span> to <span style="color:{A};">MID</span> or '
                    f'<span style="color:{R};">BAD</span>.</div><div style="margin-top:14px;display:flex;gap:8px;">'
                    f'<span class="badge-good">K=1: Max Sensitivity (Raw)</span><span class="badge-mid">K=3: Recommended Balance</span>'
                    f'<span class="badge-bad">K=8: Ultra-Conservative</span></div></div>', unsafe_allow_html=True)
    with t2:
        st.markdown(f'<div class="telemetry-card">{title("Quantile Split Calibration Envelope")}{body}'
                    f'The anomaly decision boundaries are learned exclusively on healthy training calibration engines:'
                    f'<br>• <span style="color:{G};font-weight:600;">Threshold 1 (q1)</span>: Cutoff for <span style="color:{G};">GOOD // NORMAL</span> (e.g. 90.0% quantile).'
                    f'<br>• <span style="color:{R};font-weight:600;">Threshold 2 (q2)</span>: Cutoff for <span style="color:{R};">BAD // ANOMALY</span> (e.g. 99.9% quantile).'
                    f'<br>• <span style="color:{A};font-weight:600;">Advisory Zone</span>: Scores between q1 and q2 form the <span style="color:{A};">MID // NEAR ANOMALY</span> alert window.'
                    f'</div></div>', unsafe_allow_html=True)

    st.markdown(f"<div style='font-size:13px;font-weight:700;color:{TEXT};margin:16px 0 8px 0;'>ESTABLISHED LEAD TIME & MISSED ENGINE RATES (FROM 03_EVALUATION)</div>",
                unsafe_allow_html=True)
    LEAD = [("CANARI", "52.0 cycles", "0.0%", "good", "Optimal Unsupervised"),
            ("One-Class SVM", "47.0 cycles", "0.0%", "good", "High Precision"),
            ("Isolation Forest", "46.0 cycles", "0.0%", "good", "Consistent"),
            ("Random Forest", "56.0 cycles", "0.0%", "good", "Top Supervised"),
            ("MLP", "49.0 cycles", "0.0%", "good", "Highest Macro-F1"),
            ("Gradient Boosting", "62.0 cycles", "0.0%", "good", "Aggressive Early Alarm"),
            ("Mahalanobis (d=1)", "182.0 cycles", "3.0%", "mid", "High False Alarms"),
            ("Autoencoder", "134.0 cycles", "14.0%", "bad", "Unreliable Alarm Floor")]
    table([("Model", 30, ""), ("Median Lead Time (RUL at 1st Alarm)", 25, "num-cell"),
           ("Missed Engines Rate", 20, "num-cell"), ("Operational Status", 25, "")],
          [[td(m, TEXT, True, ""), td(lt, TEXT), td(me, G if me == "0.0%" else R, True),
            f'<td><span class="badge-{b}">{s}</span></td>'] for m, lt, me, b, s in LEAD])

# ---------------- footer ----------------
st.markdown(f'<div style="border-top:1px solid #23252b;padding-top:12px;margin-top:30px;font-size:11px;color:#6b7280;display:flex;justify-content:space-between;">'
            f'<div>AERO-CMAPSS Telemetry Engine // NASA Turbofan Degradation Benchmark</div>'
            f'<div>Run: {V2_RUN_DIR.name} (v2, 28 features)</div></div>', unsafe_allow_html=True)