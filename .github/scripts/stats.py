"""Genera assets/estadisticas.svg y assets/actividad-grafico.svg con datos de la API de GitHub."""
import json, os, urllib.request
from datetime import date, timedelta
from xml.sax.saxutils import escape

owner = os.environ["GITHUB_REPOSITORY_OWNER"]
tok = os.environ.get("GITHUB_TOKEN", "")

def api(url, data=None):
    req = urllib.request.Request(url, data=data, headers={"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json"})
    return json.load(urllib.request.urlopen(req))

Q = """query($l:String!){user(login:$l){followers{totalCount}
 repositories(first:100,privacy:PUBLIC,isFork:false){totalCount nodes{stargazerCount}}
 contributionsCollection{totalCommitContributions totalPullRequestContributions totalIssueContributions totalPullRequestReviewContributions
  contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}"""
u = api("https://api.github.com/graphql", json.dumps({"query": Q, "variables": {"l": owner}}).encode())["data"]["user"]
cc = u["contributionsCollection"]
days = [d for w in cc["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
repos = [r for r in api(f"https://api.github.com/users/{owner}/repos?per_page=100") if not r["fork"]]
langs = {}
for r in repos:
    for k, v in api(r["languages_url"]).items():
        langs[k] = langs.get(k, 0) + v
tot = sum(langs.values()) or 1
top = sorted(langs.items(), key=lambda x: -x[1])[:5]
stars = sum(r["stargazerCount"] for r in u["repositories"]["nodes"])

by = {d["date"]: d["contributionCount"] for d in days}
today = date.today(); streak = 0; d = today
if by.get(d.isoformat(), 0) == 0: d -= timedelta(days=1)
while by.get(d.isoformat(), 0) > 0: streak += 1; d -= timedelta(days=1)
best = cur = 0
for x in days:
    cur = cur + 1 if x["contributionCount"] > 0 else 0; best = max(best, cur)

BG, CARD = "#0b0d12", "#0f121a"
FONT = "'Segoe UI','Helvetica Neue',Arial,sans-serif"; MONO = "'Consolas','Fira Code','DejaVu Sans Mono',monospace"
STYLE = f"""<style>
 .lab {{ font: 500 12px {MONO}; letter-spacing: 3px; }}
 .num {{ font: 800 40px {FONT}; fill: #fff; }}
 .sub {{ font: 400 13px {FONT}; fill: #7f849c; }}
 .t {{ font: 600 14px {FONT}; fill: #c0caf5; }}
 .p {{ font: 600 13px {MONO}; fill: #7aa2f7; }}
 .dot {{ animation: pulse 2.4s ease-in-out infinite; }}
 .in {{ opacity: 0; animation: in .8s ease-out forwards; }}
 .bar {{ transform-box: fill-box; transform-origin: left; transform: scaleX(0); animation: grow 1.4s cubic-bezier(.2,.7,.2,1) forwards; }}
 .cell {{ opacity: 0; animation: in .5s ease-out forwards; }}
 .sw {{ animation: sw 7s ease-in-out infinite; }}
 @keyframes pulse {{ 0%,100% {{ opacity: .35; }} 50% {{ opacity: 1; }} }}
 @keyframes in {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: none; }} }}
 @keyframes grow {{ to {{ transform: scaleX(1); }} }}
 @keyframes sw {{ from {{ transform: translateX(-300px); }} to {{ transform: translateX(1200px); }} }}
 @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} .in,.cell {{ opacity: 1; }} .bar {{ transform: none; }} }}
</style>"""
DEFS = """<linearGradient id="g" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#7aa2f7"/><stop offset="1" stop-color="#bb9af7"/></linearGradient>
<linearGradient id="beam" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#7aa2f7" stop-opacity="0"/><stop offset=".5" stop-color="#7aa2f7" stop-opacity=".16"/><stop offset="1" stop-color="#7aa2f7" stop-opacity="0"/></linearGradient>"""

def card(x, y, w, h, color, delay=0):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{CARD}" stroke="{color}" stroke-opacity=".38" stroke-width="1.2"/>'

def svg(w, h, label, body, clip):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(label)}">\n<defs>{DEFS}{STYLE}'
            f'<clipPath id="c">{clip}</clipPath></defs>\n<rect width="{w}" height="{h}" fill="{BG}"/>\n{body}\n'
            f'<g clip-path="url(#c)"><rect class="sw" x="0" y="0" width="300" height="{h}" fill="url(#beam)"/></g>\n</svg>\n')

# ---- estadísticas ----
items = [("COMMITS", cc["totalCommitContributions"], "últimos 12 meses", "#7aa2f7"),
         ("RACHA", streak, f"días seguidos · mejor {best}", "#bb9af7"),
         ("REPOSITORIOS", u["repositories"]["totalCount"], f"públicos · {stars} ★", "#bb9af7"),
         ("SEGUIDORES", u["followers"]["totalCount"], "en GitHub", "#7aa2f7")]
b = ""
for i, (lab, n, sub, c) in enumerate(items):
    x, y = 10 + (i % 2) * 295, 10 + (i // 2) * 120
    b += card(x, y, 285, 110, c)
    b += f'<circle class="dot" cx="{x+26}" cy="{y+28}" r="4" fill="{c}" style="animation-delay:{i*.3}s"/><text class="lab" x="{x+40}" y="{y+32}" fill="{c}">{lab}</text>'
    b += f'<g class="in" style="animation-delay:{.2+i*.15}s"><text class="num" x="{x+24}" y="{y+78}">{n}</text><text class="sub" x="{x+24+len(str(n))*24+14}" y="{y+78}">{escape(sub)}</text></g>'
b += card(610, 10, 580, 230, "#7aa2f7")
b += '<circle class="dot" cx="636" cy="38" r="4" fill="#7aa2f7"/><text class="lab" x="650" y="42" fill="#7aa2f7">LENGUAJES</text>'
for i, (k, v) in enumerate(top):
    y = 66 + i * 34; pct = v / tot * 100; bw = max(6, 330 * pct / 100 / (top[0][1] / tot) if top else 6)
    b += f'<g class="in" style="animation-delay:{.2+i*.12}s"><text class="t" x="636" y="{y+14}">{escape(k)}</text><rect x="760" y="{y+3}" width="330" height="14" rx="7" fill="#171b27"/>'
    b += f'<rect class="bar" x="760" y="{y+3}" width="{bw:.0f}" height="14" rx="7" fill="url(#g)" style="animation-delay:{.3+i*.12}s"/><text class="p" x="1170" y="{y+15}" text-anchor="end">{pct:.1f}%</text></g>'
if not top: b += '<text class="sub" x="636" y="100">Sin datos todavía</text>'
open("assets/estadisticas.svg", "w", encoding="utf-8").write(svg(1200, 250, "Estadísticas de GitHub", b, '<rect x="10" y="10" width="1180" height="230" rx="16"/>'))

# ---- actividad ----
weeks = cc["contributionCalendar"]["weeks"]
mx = max([d["contributionCount"] for d in days] + [1])
cols = ["#171b27", "#2b3a6b", "#4a63b8", "#7aa2f7", "#bb9af7"]
def lvl(n): return 0 if n == 0 else 1 + min(3, int((n - 1) * 4 / mx))
b = card(10, 10, 800, 240, "#7aa2f7") + card(820, 10, 370, 240, "#bb9af7")
b += f'<circle class="dot" cx="36" cy="38" r="4" fill="#7aa2f7"/><text class="lab" x="50" y="42" fill="#7aa2f7">CONTRIBUCIONES</text><text class="sub" x="790" y="42" text-anchor="end">{cc["contributionCalendar"]["totalContributions"]} en el último año</text>'
for wi, wk in enumerate(weeks):
    for d in wk["contributionDays"]:
        di = date.fromisoformat(d["date"]).weekday(); di = (di + 1) % 7
        b += f'<rect class="cell" x="{30+wi*14.4:.1f}" y="{66+di*22}" width="12" height="12" rx="3" fill="{cols[lvl(d["contributionCount"])]}" style="animation-delay:{wi*.03:.2f}s"/>'
b += '<text class="sub" x="30" y="236">menos</text>' + "".join(f'<rect x="{76+i*16}" y="226" width="11" height="11" rx="3" fill="{c}"/>' for i, c in enumerate(cols)) + '<text class="sub" x="164" y="236">más</text>'
b += '<circle class="dot" cx="846" cy="38" r="4" fill="#bb9af7"/><text class="lab" x="860" y="42" fill="#bb9af7">TIPO DE ACTIVIDAD</text>'
kinds = [("Commits", cc["totalCommitContributions"]), ("Pull requests", cc["totalPullRequestContributions"]), ("Issues", cc["totalIssueContributions"]), ("Revisiones", cc["totalPullRequestReviewContributions"])]
km = max([v for _, v in kinds] + [1])
for i, (k, v) in enumerate(kinds):
    y = 70 + i * 40
    b += f'<g class="in" style="animation-delay:{.3+i*.12}s"><text class="t" x="846" y="{y+12}">{k}</text><text class="p" x="1164" y="{y+12}" text-anchor="end">{v}</text><rect x="846" y="{y+20}" width="318" height="8" rx="4" fill="#171b27"/>'
    b += f'<rect class="bar" x="846" y="{y+20}" width="{max(6, 318*v/km):.0f}" height="8" rx="4" fill="url(#g)" style="animation-delay:{.4+i*.12}s"/></g>'
open("assets/actividad-grafico.svg", "w", encoding="utf-8").write(svg(1200, 260, "Actividad en GitHub", b, '<rect x="10" y="10" width="1180" height="240" rx="16"/>'))
print("ok", streak, best, top[:2])
