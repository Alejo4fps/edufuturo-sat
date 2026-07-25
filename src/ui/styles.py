APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@600;700;800&family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,400,0,0&display=swap');

:root {
    --navy: #102A43;
    --navy-deep: #091C2D;
    --blue: #176B87;
    --teal: #17A589;
    --mint: #E7F7F3;
    --surface: #FFFFFF;
    --canvas: #F5F8FB;
    --border: #E4EBF2;
    --text: #172B3A;
    --muted: #6B7C8F;
    --danger: #E5484D;
    --warning: #F5A524;
    --success: #22A06B;
}

html, body, [class*="css"] { font-family: "DM Sans", sans-serif; color: var(--text); }
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at 82% 4%, rgba(23,165,137,.075), transparent 24rem),
        radial-gradient(circle at 12% 92%, rgba(23,107,135,.055), transparent 27rem),
        var(--canvas);
}
[data-testid="stHeader"] {
    background:rgba(245,248,251,.86);
    backdrop-filter:blur(12px);
    height:3.35rem;
    border-bottom:1px solid rgba(228,235,242,.72);
}

/*
 * El botón para abrir la barra lateral vive dentro de stToolbar.
 * Ocultar el toolbar completo impide recuperar el menú una vez contraído.
 */
[data-testid="stToolbar"] { display:flex !important; }
[data-testid="stToolbar"] button:not([data-testid="stExpandSidebarButton"]) { display:none !important; }
[data-testid="stToolbar"] [data-testid="stStatusWidget"],
[data-testid="stToolbar"] [data-testid="stAppDeployButton"],
[data-testid="stToolbar"] [data-testid="stMainMenu"] { display:none !important; }
[data-testid="stExpandSidebarButton"] {
    display:inline-flex !important;
    position:fixed !important;
    top:.55rem;
    left:.72rem;
    width:2.35rem;
    height:2.35rem;
    align-items:center;
    justify-content:center;
    color:white !important;
    background:linear-gradient(135deg,var(--navy),#174E64) !important;
    border:1px solid rgba(255,255,255,.14) !important;
    border-radius:12px !important;
    box-shadow:0 8px 24px rgba(16,42,67,.22) !important;
    transition:transform .18s ease, box-shadow .18s ease !important;
    z-index:999999 !important;
}
[data-testid="stExpandSidebarButton"]:hover {
    transform:translateY(-1px);
    box-shadow:0 11px 28px rgba(16,42,67,.3) !important;
}
[data-testid="stExpandSidebarButton"] svg { fill:white !important; }
[data-testid="stDecoration"], #MainMenu { display:none !important; }

[data-testid="stSidebar"] {
    background:
        radial-gradient(circle at 18% 2%, rgba(23,165,137,.2), transparent 13rem),
        linear-gradient(180deg,var(--navy-deep) 0%,#0D2438 56%,#0A2031 100%);
    border-right:1px solid rgba(255,255,255,.06);
    box-shadow:12px 0 35px rgba(9,28,45,.09);
}
[data-testid="stSidebar"] * { color: #E8F0F7; }
[data-testid="stSidebarContent"] { padding-top:.4rem; }
[data-testid="stSidebarCollapseButton"] button {
    background:rgba(255,255,255,.055) !important;
    border:1px solid rgba(255,255,255,.08) !important;
    border-radius:10px !important;
    transition:background .18s ease, transform .18s ease;
}
[data-testid="stSidebarCollapseButton"] button:hover {
    background:rgba(255,255,255,.11) !important;
    transform:translateX(-1px);
}
[data-testid="stSidebar"] .stButton button {
    background: transparent; color: #C6D5E3; border: 1px solid transparent;
    border-radius: 11px; padding: .66rem .78rem; text-align: left;
    min-height:2.72rem;
    transition:background .18s ease, color .18s ease, transform .18s ease, border-color .18s ease;
}
[data-testid="stSidebar"] .stButton button:hover {
    background:rgba(255,255,255,.075);
    border-color:rgba(255,255,255,.055);
    color:white;
    transform:translateX(2px);
}
[data-testid="stSidebar"] .stButton button[kind="primary"] {
    background: linear-gradient(135deg, #17A589, #177D9A); color: white;
    border-color:rgba(255,255,255,.12);
    box-shadow:0 8px 22px rgba(23,165,137,.24);
}
[data-testid="stSidebar"] .stButton button p { font-weight:650; }

h1, h2, h3, h4, h5 { font-family: "Manrope", sans-serif; color: var(--navy); letter-spacing: -.025em; }
.block-container { max-width: 1440px; padding-top:1.35rem; padding-bottom:3.5rem; }
footer { visibility: hidden; }

.material-symbols-rounded {
    font-family:"Material Symbols Rounded";
    font-weight:normal;
    font-style:normal;
    line-height:1;
    letter-spacing:normal;
    text-transform:none;
    white-space:nowrap;
    word-wrap:normal;
    direction:ltr;
    -webkit-font-feature-settings:"liga";
    -webkit-font-smoothing:antialiased;
}

.ef-brand { padding:.15rem .15rem 1.1rem; }
.ef-brand-row { display:flex; align-items:center; gap:.75rem; }
.ef-logo {
    width:44px; height:44px; border-radius:14px; display:flex; align-items:center; justify-content:center;
    color:white; font:800 15px "Manrope"; background:linear-gradient(135deg,#17A589,#176B87);
    box-shadow:0 9px 24px rgba(23,165,137,.3);
    border:1px solid rgba(255,255,255,.16);
}
.ef-brand-name { font:800 19px "Manrope"; color:#FFF; }
.ef-brand-sub { color:#90A8BB; font-size:10.7px; line-height:1.25; margin-top:3px; max-width:185px; }
.ef-system-state {
    display:flex;
    align-items:center;
    gap:.42rem;
    margin-top:.9rem;
    padding:.48rem .6rem;
    border:1px solid rgba(121,224,204,.14);
    border-radius:10px;
    background:rgba(23,165,137,.075);
    color:#B8D6D2;
    font-size:10.5px;
    font-weight:650;
}
.ef-state-dot,.page-status-dot {
    width:7px;
    height:7px;
    border-radius:50%;
    background:#48D7B9;
    box-shadow:0 0 0 4px rgba(72,215,185,.1);
}
.ef-state-period { margin-left:auto; color:#79E0CC; font-weight:800; }
.ef-sidebar-section {
    color:#7890A4;
    text-transform:uppercase;
    letter-spacing:.13em;
    font-size:9.5px;
    font-weight:800;
    margin:1rem .25rem .5rem;
}
.ef-profile {
    margin-top:.7rem;
    padding:.78rem .82rem;
    border:1px solid rgba(255,255,255,.085);
    background:rgba(255,255,255,.038);
    border-radius:12px;
}
.ef-profile strong { display:block; color:#FFF; font-size:13px; }
.ef-profile span { color:#8FA7BA; font-size:11.5px; }
.ef-sidebar-help {
    display:flex;
    align-items:center;
    gap:.65rem;
    margin-top:1rem;
    padding-top:1rem;
    border-top:1px solid rgba(255,255,255,.07);
}
.ef-sidebar-help > span {
    display:flex;
    align-items:center;
    justify-content:center;
    width:30px;
    height:30px;
    border-radius:9px;
    color:#79E0CC;
    background:rgba(23,165,137,.12);
    border:1px solid rgba(121,224,204,.15);
    font:800 10px "Manrope";
}
.ef-sidebar-help strong { display:block; font-size:10.5px; color:#C8D7E3; }
.ef-sidebar-help small { display:block; margin-top:1px; font-size:9.5px; color:#6F899E; }

.page-heading {
    display:flex;
    align-items:flex-end;
    justify-content:space-between;
    gap:1.5rem;
    margin-bottom:1.45rem;
    padding-bottom:1rem;
    border-bottom:1px solid var(--border);
}
.page-heading-copy { min-width:0; }
.page-kicker { color:var(--teal); font-weight:800; font-size:11px; text-transform:uppercase; letter-spacing:.12em; margin-bottom:.3rem; }
.page-heading h1 { font-size:31px; line-height:1.15; margin:0; }
.page-heading p { margin:.38rem 0 0; color:var(--muted); font-size:14px; max-width:720px; }
.page-heading-status {
    display:inline-flex;
    align-items:center;
    gap:.5rem;
    flex:0 0 auto;
    margin-bottom:.15rem;
    padding:.48rem .7rem;
    border:1px solid #D9E8E7;
    border-radius:999px;
    color:#4C6A72;
    background:rgba(255,255,255,.74);
    box-shadow:0 4px 14px rgba(18,49,71,.035);
    font-size:10.5px;
    font-weight:750;
}

.metric-card {
    background:linear-gradient(145deg,#FFFFFF 0%,#FBFDFE 100%);
    border:1px solid rgba(220,229,237,.95);
    border-radius:17px;
    padding:1rem 1.1rem;
    box-shadow:0 6px 22px rgba(18,49,71,.055);
    min-height:126px;
    position:relative;
    overflow:hidden;
    transition:transform .2s ease, box-shadow .2s ease, border-color .2s ease;
}
.metric-card:hover {
    transform:translateY(-2px);
    border-color:color-mix(in srgb,var(--accent,#17A589) 25%,#DCE5ED);
    box-shadow:0 12px 28px rgba(18,49,71,.085);
}
.metric-card:after { content:""; position:absolute; left:0; top:0; bottom:0; width:4px; background:var(--accent,#17A589); }
.metric-card:before {
    content:"";
    position:absolute;
    width:90px;
    height:90px;
    top:-52px;
    right:-42px;
    border-radius:50%;
    background:var(--accent,#17A589);
    opacity:.055;
}
.metric-card-top { display:flex; align-items:center; justify-content:space-between; gap:.7rem; }
.metric-label { color:var(--muted); font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:.07em; }
.metric-icon {
    display:flex;
    align-items:center;
    justify-content:center;
    width:29px;
    height:29px;
    flex:0 0 29px;
    border-radius:9px;
    color:var(--accent,#17A589);
    background:color-mix(in srgb,var(--accent,#17A589) 10%,white);
    font-size:17px;
}
.metric-value { color:var(--navy); font:800 28px "Manrope"; margin:.25rem 0 .1rem; }
.metric-help { color:#8191A2; font-size:12px; line-height:1.35; }

.objective-card {
    background:
        radial-gradient(circle at 92% 5%,rgba(121,224,204,.14),transparent 11rem),
        linear-gradient(135deg,#102A43,#174E64);
    border:1px solid rgba(255,255,255,.07);
    border-radius:18px;
    padding:1.28rem 1.42rem;
    color:white;
    box-shadow:0 13px 32px rgba(16,42,67,.17);
}
.objective-card .eyebrow { color:#79E0CC; font-size:10px; font-weight:800; letter-spacing:.13em; text-transform:uppercase; }
.objective-card h3 { color:white; font-size:18px; line-height:1.35; margin:.4rem 0 .55rem; }
.objective-card p { color:#B9CCD9; font-size:12.5px; margin:0; }

.section-card { background:white; border:1px solid var(--border); border-radius:17px; padding:1.1rem 1.2rem; box-shadow:0 5px 20px rgba(18,49,71,.045); }
.section-title { font:700 15px "Manrope"; color:var(--navy); margin-bottom:.15rem; }
.section-subtitle { font-size:12px; color:var(--muted); margin-bottom:.7rem; }

.risk-badge { display:inline-flex; align-items:center; gap:.4rem; border-radius:999px; padding:.3rem .65rem; font-size:11.5px; font-weight:800; }
.risk-dot { width:7px; height:7px; border-radius:50%; }
.risk-alto { color:#C93137; background:#FDEBEC; }
.risk-medio { color:#A86400; background:#FFF3D6; }
.risk-bajo { color:#147A50; background:#E5F6EE; }
.data-badge { display:inline-block; border-radius:7px; padding:.25rem .5rem; font-size:10.5px; font-weight:800; letter-spacing:.03em; }
.data-evaluated { color:#147A50; background:#E5F6EE; }
.data-pending { color:#8A5B0A; background:#FFF1D6; }

.student-row { display:flex; align-items:center; justify-content:space-between; gap:1rem; padding:.8rem .1rem; border-bottom:1px solid #EDF1F5; }
.student-row { transition:background .16s ease, padding .16s ease; border-radius:10px; }
.student-row:hover { background:#F7FAFC; padding-left:.45rem; padding-right:.45rem; }
.student-row:last-child { border-bottom:none; }
.student-main { display:flex; align-items:center; gap:.7rem; min-width:0; }
.avatar { width:38px; height:38px; flex:0 0 38px; display:flex; align-items:center; justify-content:center; border-radius:12px; color:white; background:linear-gradient(135deg,#176B87,#17A589); font:800 12px "Manrope"; }
.student-name { color:var(--navy); font-weight:700; font-size:13.5px; }
.student-meta { color:var(--muted); font-size:11.5px; margin-top:2px; }

.info-strip { border:1px solid #CAE7E1; background:#F0FAF7; border-radius:13px; padding:.8rem 1rem; color:#245B52; font-size:12.5px; }
.warning-strip { border:1px solid #F5D69D; background:#FFF8E8; border-radius:13px; padding:.8rem 1rem; color:#795215; font-size:12.5px; }
.result-hero { border-radius:18px; padding:1.2rem 1.35rem; color:white; background:linear-gradient(135deg,#102A43,#176B87); }
.result-hero .score { font:800 42px "Manrope"; }
.result-hero .caption { color:#C5D9E4; font-size:12px; }
.action-card {
    background:
        radial-gradient(circle at 96% 0%,rgba(23,165,137,.09),transparent 10rem),
        linear-gradient(135deg,#F0FAF7,#EAF4FA);
    border:1px solid #CBE4E5;
    border-radius:17px;
    padding:1.12rem 1.22rem;
    box-shadow:0 5px 18px rgba(18,49,71,.035);
}
.action-card h3 { margin:0 0 .3rem; font-size:17px; }
.action-card p { margin:0; color:#587084; font-size:12.5px; line-height:1.5; }

.run-proof {
    display:grid;
    grid-template-columns:1.15fr 1fr 1fr 1fr;
    gap:1px;
    margin:.9rem 0 1.15rem;
    overflow:hidden;
    border:1px solid #D6E5EA;
    border-radius:16px;
    background:#D6E5EA;
    box-shadow:0 7px 24px rgba(18,49,71,.055);
}
.run-proof > div {
    min-width:0;
    padding:.85rem 1rem;
    background:linear-gradient(145deg,#FFFFFF,#F8FBFC);
}
.run-proof span {
    display:block;
    color:#7B8C9C;
    font-size:9px;
    font-weight:850;
    letter-spacing:.1em;
    margin-bottom:.28rem;
}
.run-proof strong {
    display:block;
    overflow:hidden;
    color:var(--navy);
    font:700 12px "Manrope";
    text-overflow:ellipsis;
    white-space:nowrap;
}
.prediction-explain {
    display:grid;
    grid-template-columns:repeat(4,minmax(0,1fr));
    gap:1px;
    margin:.75rem 0 1rem;
    overflow:hidden;
    border:1px solid #D9E7EB;
    border-radius:15px;
    background:#D9E7EB;
}
.prediction-explain > div {
    padding:.9rem 1rem;
    background:linear-gradient(145deg,#FFFFFF,#F7FBFC);
}
.prediction-explain .explain-label {
    display:block;
    min-height:27px;
    color:#748697;
    font-size:10px;
    font-weight:750;
    line-height:1.3;
    text-transform:uppercase;
    letter-spacing:.045em;
}
.prediction-explain strong {
    display:block;
    color:var(--navy);
    font:800 15px "Manrope";
}
.factor-list {
    display:flex;
    flex-wrap:wrap;
    gap:.45rem;
    margin:.5rem 0 1.1rem;
}
.factor-chip {
    display:inline-flex;
    align-items:center;
    padding:.38rem .62rem;
    border:1px solid #CDE7E1;
    border-radius:999px;
    color:#176454;
    background:#EFFAF7;
    font-size:11px;
    font-weight:750;
}
.evidence-note {
    display:flex;
    align-items:flex-start;
    gap:.85rem;
    margin:.2rem 0 1rem;
    padding:1rem 1.1rem;
    border:1px solid #C9E5DE;
    border-radius:16px;
    background:linear-gradient(135deg,#F0FAF7,#F4F9FC);
}
.evidence-note .evidence-icon {
    display:flex;
    align-items:center;
    justify-content:center;
    width:38px;
    height:38px;
    flex:0 0 38px;
    border-radius:12px;
    color:#147A65;
    background:#DDF5EF;
}
.evidence-note strong {
    display:block;
    color:var(--navy);
    font:750 14px "Manrope";
}
.evidence-note p {
    max-width:900px;
    margin:.25rem 0 0;
    color:#587084;
    font-size:12.5px;
    line-height:1.5;
}
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap:.3rem;
    padding:.28rem;
    border:1px solid var(--border);
    border-radius:13px;
    background:rgba(255,255,255,.78);
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    min-height:2.65rem;
    padding:.55rem .9rem;
    border-radius:10px;
    color:#627587;
    font-weight:700;
}
[data-testid="stTabs"] [aria-selected="true"] {
    color:var(--navy);
    background:#EDF7F5;
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { display:none; }

div[data-testid="stVerticalBlockBorderWrapper"] {
    background:rgba(255,255,255,.92);
    border-color:var(--border);
    border-radius:17px;
    box-shadow:0 5px 20px rgba(18,49,71,.04);
}
div[data-testid="stForm"] { background:white; border:1px solid var(--border); border-radius:17px; padding:1.1rem; box-shadow:0 5px 20px rgba(18,49,71,.035); }
.stTextInput input, .stNumberInput input, .stSelectbox [data-baseweb="select"] > div, .stTextArea textarea, .stDateInput input {
    border-radius:11px !important;
    border-color:#DDE6EE !important;
    background:#FBFDFE !important;
    transition:border-color .16s ease, box-shadow .16s ease !important;
}
.stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
    border-color:#66BFAE !important;
    box-shadow:0 0 0 3px rgba(23,165,137,.09) !important;
}
.stButton button, .stDownloadButton button, .stFormSubmitButton button {
    border-radius:11px;
    font-weight:750;
    transition:transform .16s ease, box-shadow .16s ease, border-color .16s ease;
}
.stButton button:hover, .stDownloadButton button:hover, .stFormSubmitButton button:hover { transform:translateY(-1px); }
.stButton button[kind="primary"], .stFormSubmitButton button[kind="primary"] {
    box-shadow:0 7px 18px rgba(23,165,137,.17);
}
[data-testid="stDataFrame"] {
    border:1px solid var(--border);
    border-radius:15px;
    overflow:hidden;
    box-shadow:0 4px 16px rgba(18,49,71,.03);
}
[data-testid="stMetric"] {
    padding:.7rem .8rem;
    border:1px solid var(--border);
    border-radius:13px;
    background:rgba(255,255,255,.8);
}
[data-testid="stPlotlyChart"] {
    background:rgba(255,255,255,.34);
    border-radius:16px;
}

@media (max-width: 900px) {
    .page-heading { display:block; }
    .page-heading-status { margin-top:.85rem; }
    .block-container { padding-left:1rem; padding-right:1rem; padding-top:1rem; }
    .run-proof, .prediction-explain { grid-template-columns:repeat(2,minmax(0,1fr)); }
}

@media (max-width: 640px) {
    .page-heading h1 { font-size:25px; }
    .page-heading p { font-size:13px; }
    [data-testid="stExpandSidebarButton"] { top:.48rem; left:.55rem; }
    .run-proof, .prediction-explain { grid-template-columns:1fr; }
}

@media (prefers-reduced-motion: reduce) {
    *, *:before, *:after {
        scroll-behavior:auto !important;
        transition-duration:.01ms !important;
        animation-duration:.01ms !important;
        animation-iteration-count:1 !important;
    }
}
</style>
"""
