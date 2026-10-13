"""Actualiza el texto dinámico de assets/estado.svg con el repo público más activo."""
import json, os, re, urllib.request
from datetime import datetime, timezone

owner = os.environ["GITHUB_REPOSITORY_OWNER"]
profile_repo = os.environ.get("GITHUB_REPOSITORY", "").split("/")[-1]
req = urllib.request.Request(
    f"https://api.github.com/users/{owner}/repos?per_page=100&sort=pushed",
    headers={"Authorization": f"Bearer {os.environ.get('GITHUB_TOKEN', '')}",
             "Accept": "application/vnd.github+json"})
repos = [r for r in json.load(urllib.request.urlopen(req))
         if not r["fork"] and not r["archived"] and r["name"] != profile_repo]
path = "assets/estado.svg"
svg = open(path, encoding="utf-8").read()
if repos:
    r = max(repos, key=lambda x: x["pushed_at"])
    secs = (datetime.now(timezone.utc) - datetime.fromisoformat(r["pushed_at"].replace("Z", "+00:00"))).total_seconds()
    m = int(secs // 60)
    if m < 60: t = "hace un momento" if m < 5 else f"hace {m} min"
    elif m < 1440: t = f"hace {m // 60} h"
    elif m < 43200: t = f"hace {m // 1440} d"
    else: t = f"hace {m // 43200} mes" + ("es" if m >= 86400 else "")
    name = r["name"] if len(r["name"]) <= 18 else r["name"][:17] + "…"
    text = f"Activo en {name} · {t}"
    svg = re.sub(r"<!--AHORA-->.*?<!--/AHORA-->", f"<!--AHORA-->{text}<!--/AHORA-->", svg)
    open(path, "w", encoding="utf-8").write(svg)
    print(text)
else:
    svg = re.sub(r"<!--AHORA-->.*?<!--/AHORA-->", "<!--AHORA-->Proyectos en desarrollo<!--/AHORA-->", svg)
    open(path, "w", encoding="utf-8").write(svg)
