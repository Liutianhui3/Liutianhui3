"""Generate local profile cards from GitHub's public API (Python standard library)."""
import json
import os
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from html import escape
from pathlib import Path
from urllib.request import Request, urlopen

USERNAME = "Liutianhui3"
OUTPUT = Path(__file__).resolve().parents[1] / "media" / "stats"


def api(path):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-stats"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    for attempt in range(3):
        try:
            with urlopen(Request("https://api.github.com" + path, headers=headers), timeout=30) as response:
                return json.load(response)
        except Exception:
            if attempt == 2:
                raise
            time.sleep(attempt + 1)


def card(title, width, height, body, subtitle):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">'
        f'<title>{escape(title)}</title>'
        '<defs><linearGradient id="bg" x2="1" y2="1"><stop stop-color="#1B1830"/>'
        '<stop offset="1" stop-color="#101320"/></linearGradient>'
        '<linearGradient id="accent"><stop stop-color="#A78BFA"/><stop offset="1" stop-color="#38BDF8"/></linearGradient>'
        '<clipPath id="bar"><rect x="28" y="103" width="424" height="12" rx="6"/></clipPath></defs>'
        f'<rect x=".5" y=".5" width="{width-1}" height="{height-1}" rx="18" fill="url(#bg)" stroke="#35304B"/>'
        '<path d="M28 1H190" stroke="url(#accent)" stroke-width="2"/>'
        '<style>text{font-family:Arial,"Microsoft YaHei",sans-serif;fill:#DCE2F2;font-size:13px}'
        '.title{fill:#F0EDFF;font-size:20px;font-weight:700}.muted{fill:#969BB5;font-size:11px}'
        '.number{fill:#F3F2FF;font-size:28px;font-weight:700;font-family:Arial,sans-serif}</style>'
        f'<text class="title" x="28" y="39">{escape(title)}</text>'
        f'<text class="muted" x="28" y="62">{escape(subtitle)}</text>'
        '<circle cx="440" cy="32" r="4" fill="#34D399"/>'
        f'{body}</svg>\n'
    )


def icon(kind, x, y, color):
    paths = {
        "repo": '<path d="M4 3h13v17H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Zm0 13h13M6 7h7"/>',
        "star": '<path d="m12 2 3 6 7 1-5 5 1 7-6-3-6 3 1-7-5-5 7-1Z"/>',
        "fork": '<circle cx="6" cy="4" r="2"/><circle cx="18" cy="4" r="2"/><circle cx="12" cy="20" r="2"/><path d="M6 6v3c0 4 12 2 12-2V6M12 12v6"/>',
        "people": '<circle cx="9" cy="7" r="4"/><path d="M2 21v-3a7 7 0 0 1 14 0v3M17 4a4 4 0 0 1 0 8M20 21v-3a7 7 0 0 0-2-5"/>',
    }
    return f'<g transform="translate({x} {y}) scale(.72)" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{paths[kind]}</g>'


def main():
    user = api(f"/users/{USERNAME}")
    repos = []
    page = 1
    while True:
        batch = api(f"/users/{USERNAME}/repos?per_page=100&page={page}")
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    owned = [repo for repo in repos if not repo["fork"]]
    languages = Counter()
    with ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(lambda repo: api(f'/repos/{USERNAME}/{repo["name"]}/languages'), owned):
            languages.update(result)
    languages.pop("C", None)
    metrics = [("公开仓库", user["public_repos"]), ("获得 Star", sum(r["stargazers_count"] for r in owned)),
               ("获得 Fork", sum(r["forks_count"] for r in owned)), ("关注者", user["followers"])]
    body = ""
    for i, ((label, value), kind, color) in enumerate(zip(
            metrics, ["repo", "star", "fork", "people"], ["#A78BFA", "#FBBF24", "#38BDF8", "#34D399"])):
        x, y = 20 + (i % 2)*224, 83 + (i // 2)*98
        body += (f'<rect x="{x}" y="{y}" width="216" height="88" rx="11" fill="#FFFFFF" fill-opacity=".025" stroke="#FFFFFF" stroke-opacity=".055"/>'
                 + icon(kind, x+16, y+15, color)
                 + f'<text x="{x+43}" y="{y+28}" class="muted">{label}</text>'
                 f'<text x="{x+17}" y="{y+66}" class="number">{value:,}</text>')
    body += '<text x="28" y="302" class="muted">PUBLIC ACTIVITY</text><text x="452" y="302" text-anchor="end" class="muted">GitHub / Liutianhui3</text>'
    stats = card("我的 GitHub 开发统计", 480, 322, body, "Liutianhui3 / 开源开发足迹")
    top = languages.most_common(6)
    total = sum(languages.values())
    palette = {"Vue": "#41B883", "JavaScript": "#F1E05A", "TypeScript": "#3178C6",
               "Python": "#58A6FF", "CSS": "#A78BFA", "Less": "#8BA4CE", "HTML": "#E34C26"}
    colors = [palette.get(name, "#FB7185") for name, _ in top]
    body = '<text x="28" y="89" class="muted">LANGUAGE DISTRIBUTION</text>'
    offset = 28
    for i, (language, size) in enumerate(top):
        percent = size / total * 100
        width = 424 * percent / 100
        body += f'<rect x="{offset:.3f}" y="103" width="{width:.3f}" height="12" fill="{colors[i]}" clip-path="url(#bar)"/>'
        offset += width
        x, y = 28 + (i % 2)*224, 149 + (i // 2)*43
        body += (f'<circle cx="{x+4}" cy="{y-4}" r="4" fill="{colors[i]}"/>'
                 f'<text x="{x+17}" y="{y}">{escape(language)}</text>'
                 f'<text x="{x+199}" y="{y}" text-anchor="end" style="fill:{colors[i]};font-weight:600">{percent:.1f}%</text>')
    if not top:
        body += '<text x="28" y="155">暂无语言数据</text>'
    body += '<path d="M28 264H452" stroke="#FFFFFF" stroke-opacity=".08"/><text x="28" y="289" class="muted">公开原创仓库 · 按代码字节统计 · 不含 C</text>'
    language_card = card("常用开发语言", 480, 322, body, "代码中的技术偏好 / TOP LANGUAGES")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "github-stats.svg").write_text(stats, encoding="utf-8")
    (OUTPUT / "top-languages.svg").write_text(language_card, encoding="utf-8")


if __name__ == "__main__":
    main()
