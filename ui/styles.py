"""All CSS (black and purple theme) and the logo helper."""
import base64
from functools import lru_cache
from pathlib import Path

LOGO = Path(__file__).resolve().parent.parent / "assets" / "logo.png"


@lru_cache(maxsize=1)
def logo_uri():
    """The logo as a data: URI so it can sit inside HTML."""
    return "data:image/png;base64," + base64.b64encode(LOGO.read_bytes()).decode()


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');
:root{--bg:#09060F;--card:#120D1F;--border:#2B1F47;--p:#8B5CF6;--p2:#A855F7;--light:#C4B5FD;--text:#EDE9FE;
--muted:#A59BC0;--green:#3FB950;--amber:#F5A524;--red:#F85149;--grad:linear-gradient(90deg,#6D28D9,#A855F7)}
html,body,[data-testid="stApp"],[data-testid="stAppViewContainer"]{background:var(--bg)!important;color:var(--text);
font-family:'Inter',sans-serif}
[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],#MainMenu,footer{display:none!important}
.block-container{max-width:1150px;padding:1rem 1.2rem 4rem!important}
h1,h2,h3,h4,p,label,span,li{font-family:'Inter',sans-serif}
code,pre,[data-testid="stCode"] *{font-family:'JetBrains Mono',monospace!important;font-size:.85rem}
a{color:var(--light)!important}
/* ---- navbar pill ---- */
.st-key-navbar{position:sticky;top:8px;z-index:50;background:rgba(18,13,31,.92);backdrop-filter:blur(10px);
border:1px solid var(--border);border-radius:999px;padding:6px 14px;margin-bottom:1.4rem;box-shadow:0 6px 30px rgba(109,40,217,.25)}
.st-key-navbar [data-testid="stHorizontalBlock"]{flex-wrap:nowrap!important;gap:.5rem!important;align-items:center}
.st-key-navbar [data-testid="stColumn"],.st-key-navbar [data-testid="column"]{min-width:0!important;display:flex;align-items:center}
.st-key-navbar [data-testid="stColumn"]:first-child,.st-key-navbar [data-testid="stColumn"]:last-child{flex:0 0 auto!important;width:auto!important}
.st-key-navbar [data-testid="stColumn"]>div,.st-key-navbar [data-testid="stColumn"] [data-testid="stVerticalBlock"]{width:100%}
.brand{display:flex;align-items:center;gap:10px;white-space:nowrap}
.brand img{height:38px;width:38px;object-fit:cover;border-radius:50%;background:#F5F3FF;padding:2px;border:2px solid #F5F3FF}
.brand span{font-weight:800;font-size:1.25rem;line-height:1;background:var(--grad);-webkit-background-clip:text;
background-clip:text;-webkit-text-fill-color:transparent}
.st-key-navbar [data-testid="stElementContainer"],.st-key-navbar [data-testid="stMarkdownContainer"]{margin:0!important;padding:0!important}
.st-key-navbar [data-testid="stVerticalBlock"]{gap:0!important;justify-content:center}
.st-key-navbar button{border-radius:999px!important;min-height:40px;height:40px}
.st-key-navbar [data-testid="stPopover"],.st-key-navbar [data-testid="stPopover"]>div{display:flex;align-items:center}
.brand{height:40px}
/* hide the link/anchor icon next to headings */
[data-testid="stHeaderActionElements"],a.anchor-link,h1 a,h2 a,h3 a,h4 a,[data-testid="stHeadingWithActionElements"] a{display:none!important}
/* ---- skill pills: rectangular blocks that glow when selected ---- */
[data-testid="stPills"] button{border-radius:10px!important;background:#0E0A18!important;border:1px solid var(--border)!important;
color:var(--muted)!important;font-weight:600;transition:all .2s ease}
[data-testid="stPills"] button:hover{border-color:var(--p)!important;color:#fff!important}
[data-testid="stPills"] button[data-testid="stBaseButton-pillsActive"],[data-testid="stPills"] button[aria-checked="true"],
[data-testid="stPills"] button[aria-pressed="true"]{border:1px solid var(--p)!important;color:#fff!important;
background:rgba(139,92,246,.18)!important;box-shadow:0 0 0 1px var(--p),0 0 14px rgba(168,85,247,.65)}
/* ---- buttons ---- */
.stButton>button,.stLinkButton>a,[data-testid="stPopover"]>button{border-radius:999px!important;border:1px solid var(--border)!important;
background:transparent!important;color:var(--text)!important;font-weight:600;transition:all .2s ease}
.stButton>button:hover,.stLinkButton>a:hover,[data-testid="stPopover"]>button:hover{border-color:var(--p)!important;
color:#fff!important;transform:translateY(-1px)}
.stButton>button[kind="primary"],[data-testid="stBaseButton-primary"]{background:var(--grad)!important;border:none!important;color:#fff!important}
/* ---- cards / inputs ---- */
[data-testid="stVerticalBlockBorderWrapper"]{background:var(--card);border-color:var(--border)!important;border-radius:16px!important;
transition:border-color .2s ease,box-shadow .2s ease}
[data-testid="stVerticalBlockBorderWrapper"]:hover{border-color:#4C3A82!important}
[class*="st-key-taskcard_sel"]{border-color:var(--p)!important;box-shadow:0 0 0 1px var(--p),0 8px 30px rgba(139,92,246,.25)}
[data-baseweb="input"],[data-baseweb="select"]>div,[data-baseweb="base-input"]{background:#0E0A18!important;border-radius:12px!important}
[data-testid="stPopoverBody"]{background:var(--card)!important;border:1px solid var(--border)!important;border-radius:16px!important}
[data-testid="stStatusWidget"],[data-testid="stExpander"]{border-color:var(--border)!important;border-radius:14px!important}
/* ---- page fade ---- */
@keyframes fadein{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
[class*="st-key-page_"]{animation:fadein .45s ease both}
.h2{font-size:1.5rem;font-weight:800;margin:1rem 0 .4rem}.h3{font-size:1.3rem;font-weight:700;margin:1rem 0 .5rem}
/* ---- hero / chips / steps ---- */
.hero{text-align:center;margin:.4rem 0 1.2rem}
.hero .h1{font-size:2.3rem;font-weight:800;margin:0;background:var(--grad);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
.hero p{color:var(--muted);margin:.3rem 0 0}
.chip{display:inline-block;padding:2px 10px;border-radius:999px;font-size:.75rem;font-weight:600;margin:2px 4px 2px 0;border:1px solid}
.muted{color:var(--muted);font-size:.9rem}.mono{font-family:'JetBrains Mono',monospace}
.step{display:flex;align-items:center;gap:12px;margin:.2rem 0 .4rem;font-weight:700;font-size:1.05rem}
.num{flex:0 0 32px;height:32px;border-radius:50%;background:var(--grad);display:flex;align-items:center;justify-content:center;font-weight:800;color:#fff}
.tcard-title{font-weight:700;margin:.3rem 0}
.score{font-size:1.6rem;font-weight:800;color:var(--light)}
/* ---- responsive ---- */
@media (max-width:900px){.block-container{padding:.6rem .8rem 3rem!important}.hero .h1{font-size:1.9rem}}
@media (max-width:640px){
 .hero .h1{font-size:1.5rem}.brand span{display:none}.st-key-navbar{padding:5px 8px}
 .st-key-navbar button,.st-key-navbar a{padding:.25rem .5rem!important;font-size:.8rem!important}
 .st-key-navbar [data-testid="stHorizontalBlock"]{gap:.25rem!important}
}

</style>
"""
