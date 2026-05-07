#!/usr/bin/env python3
"""Generate dynamic sections for the GitHub profile README."""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any


README_PATH = "README.md"
GITHUB_USER = "chochy2001"
ORG = "CAPDESIS"
API_ROOT = "https://api.github.com"

BLOCKS = {
    "apps": ("<!-- APPS:START -->", "<!-- APPS:END -->"),
    "courses": ("<!-- COURSES:START -->", "<!-- COURSES:END -->"),
    "stats": ("<!-- PROFILE-STATS:START -->", "<!-- PROFILE-STATS:END -->"),
    "activity": ("<!-- PRIVATE-ACTIVITY:START -->", "<!-- PRIVATE-ACTIVITY:END -->"),
}

PRODUCTS = [
    {
        "name": "Ingeniería Tracker",
        "emoji": "🧭",
        "status": "LIVE",
        "status_color": "22c55e",
        "icon": "https://play-lh.googleusercontent.com/s1irh98NALmdY6n_0mhC3xp-AxwSQaI6j1PkmpfI0L0SkvLMqFUvj8HleSst4U3SytiF=w240-h480-rw",
        "summary": "UNAM engineering companion for professors, ratings, campus routing, schedules, exports, progress tracking, and study workflows.",
        "tags": ["Flutter", "Go", "iOS", "Android", "Web"],
        "links": [("Website", "https://ingenieriatracker.com/")],
        "match": [r"ingenieria", r"ingetracker", r"basesdatosing"],
    },
    {
        "name": "Formulae Pro & Community",
        "short_name": "Formulae",
        "emoji": "∑",
        "status": "LIVE",
        "status_color": "22c55e",
        "icon": "https://play-lh.googleusercontent.com/5kLMnce84PkTt4hQEnvN5iWW8FJUqlm07R7Y-V5dYch9KPloLLUghyDw9_a611A6DA=s180-rw",
        "summary": "Math and science apps with formulas, search, favorites, exercises, media, PDF downloads, and on-demand help.",
        "tags": ["Flutter", "Firebase", "Android", "iOS", "Web"],
        "links": [("Website", "https://formulaeapps.com/en/")],
        "match": [r"formulae"],
    },
    {
        "name": "Capmenu",
        "emoji": "🍽️",
        "status": "IN DEVELOPMENT",
        "status_color": "d97706",
        "icon": "https://capmenu.com/imagenes/capmenu_landing_menu.png",
        "summary": "Digital menu and restaurant operations platform with QR menus, real-time edits, staff roles, tables, pricing, and tiers.",
        "tags": ["Flutter", "PHP", "QR", "Restaurants SaaS"],
        "links": [("Landing", "https://capmenu.com/"), ("App", "https://app.capmenu.com/")],
        "match": [r"capmenu", r"menurestaurante"],
    },
    {
        "name": "Cap Living",
        "emoji": "🏠",
        "status": "IN DEVELOPMENT",
        "status_color": "d97706",
        "icon": "https://capliving.mx/logo.png?v=20260501c",
        "summary": "Residential operations product for incidents, amenity booking, announcements, administration, analytics, and resident workflows.",
        "tags": ["Flutter", "Go", "Residential", "Admin"],
        "links": [("Website", "https://capliving.mx/")],
        "match": [r"capliving"],
    },
    {
        "name": "Lo Más Fresh",
        "emoji": "🥬",
        "status": "LIVE",
        "status_color": "22c55e",
        "icon": "https://lomasfresh.com/brand/app-icon-256.png",
        "summary": "Fresh-produce marketplace connecting local providers with buyers through catalog, cart, orders, dashboards, and offline-tolerant flows.",
        "tags": ["Flutter", "Go", "Marketplace", "Orders"],
        "links": [("Website", "https://lomasfresh.com/")],
        "match": [r"lo_mas_fresh", r"lomasfresh"],
    },
    {
        "name": "CapTienda",
        "emoji": "🛒",
        "status": "IN DEVELOPMENT",
        "status_color": "d97706",
        "icon": "https://capdesis.com/images/products/captienda_logo.svg",
        "summary": "Point of sale and retail management for small shops: inventory, sales, multi-location operations, backend, and owner dashboard.",
        "tags": ["Flutter", "Go", "POS", "Retail"],
        "links": [("Website", "https://captienda.com/")],
        "match": [r"captienda", r"pos_tienda", r"pos_backend"],
    },
    {
        "name": "OmniMon",
        "emoji": "🛡️",
        "status": "LIVE",
        "status_color": "22c55e",
        "icon": "https://omnimon.com.mx/favicon.svg",
        "summary": "Cross-platform system monitor with native telemetry, MITRE mapping, NIST heartbeat, package distribution, and security workflows.",
        "tags": ["Rust", "Tauri", "Svelte", "Telemetry"],
        "links": [("Website", "https://omnimon.com.mx/"), ("GitHub", "https://github.com/chochy2001/omnimon")],
        "match": [r"omnimon"],
    },
    {
        "name": "Capdesis",
        "emoji": "🚀",
        "status": "LIVE",
        "status_color": "22c55e",
        "icon": "https://capdesis.com/images/logo/capdesis_logo.webp",
        "summary": "Company website, product infrastructure, landing pages, deployment operations, and shared product work.",
        "tags": ["Astro", "Automation", "Web", "Product ops"],
        "links": [("Website", "https://capdesis.com/")],
        "match": [r"capdesisweb", r"capdesis.*landing"],
    },
    {
        "name": "Portfolio",
        "emoji": "👨‍💻",
        "status": "LIVE",
        "status_color": "22c55e",
        "icon": "https://jorgesalgadomiranda.com/og.png",
        "summary": "Personal site for my professional work, products, courses, and contact links.",
        "tags": ["Personal site", "Projects", "Courses", "Contact"],
        "links": [("Website", "https://jorgesalgadomiranda.com/")],
        "match": [r"jorgesalgadomiranda"],
    },
]

COURSES = [
    {
        "icon": "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/c/c-original.svg",
        "name": "C from zero to expert",
        "topic": "Programming fundamentals and C",
        "url": "https://www.udemy.com/course/programacion_en_c_desde_cero_a_experto/?referralCode=D0CF1FABF59B2D29079B",
    },
    {
        "icon": "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/go/go-original.svg",
        "name": "Golang",
        "topic": "Backend and systems programming",
        "url": "https://www.udemy.com/course/programacion-go/?referralCode=414BED159CC7E73DFE03",
    },
    {
        "icon": "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/git/git-original.svg",
        "name": "Git and GitHub",
        "topic": "Version control workflow",
        "url": "https://www.udemy.com/course/git-y-github-desde-cero-a-experto/?referralCode=D1D66BA1BD00C54733FF",
    },
    {
        "icon": "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/photoshop/photoshop-original.svg",
        "name": "Photoshop",
        "topic": "Design fundamentals",
        "url": "https://www.udemy.com/course/introduccion-a-adobe-photoshop-cc-2020-actualizado/?referralCode=B156AD3A3E7122C398DB",
    },
    {
        "icon": "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/vim/vim-original.svg",
        "name": "Vim",
        "topic": "Editor workflow",
        "url": "https://www.udemy.com/course/chochy_vim/?referralCode=E79B7EB4B6A5E52CD97D",
    },
    {
        "icon": "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg",
        "name": "Programming in multiple languages",
        "topic": "Cross-language foundations",
        "url": "https://www.udemy.com/course/programacion-todosloslenguajes/?referralCode=3CD9F2EE23F4EAAFD5F0",
    },
]


class GitHubError(RuntimeError):
    def __init__(self, url: str, status: int, message: str) -> None:
        super().__init__(f"{url} returned {status}: {message}")
        self.url = url
        self.status = status
        self.message = message


def github_token() -> str:
    return (
        os.environ.get("PROFILE_STATS_TOKEN")
        or os.environ.get("GH_TOKEN")
        or os.environ.get("GITHUB_TOKEN")
        or ""
    )


def has_private_token() -> bool:
    return bool(os.environ.get("PROFILE_STATS_TOKEN") or os.environ.get("GH_TOKEN"))


def api_request(path_or_url: str, token: str) -> tuple[Any, dict[str, str]]:
    url = path_or_url if path_or_url.startswith("http") else f"{API_ROOT}{path_or_url}"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "chochy2001-profile-readme",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = response.read().decode("utf-8")
            parsed = json.loads(data) if data else None
            return parsed, {key.lower(): value for key, value in response.headers.items()}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise GitHubError(url, exc.code, body[:240]) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"{url} failed: {exc.reason}") from exc


def api_json(path_or_url: str, token: str) -> Any:
    data, _headers = api_request(path_or_url, token)
    return data


def api_pages(path: str, token: str) -> list[dict[str, Any]]:
    url = f"{API_ROOT}{path}"
    items: list[dict[str, Any]] = []
    while url:
        page, headers = api_request(url, token)
        if isinstance(page, list):
            items.extend(page)
        link = headers.get("link", "")
        next_url = ""
        for part in link.split(","):
            if 'rel="next"' in part:
                match = re.search(r"<([^>]+)>", part)
                if match:
                    next_url = match.group(1)
        url = next_url
    return items


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    if value.endswith("Z"):
        value = f"{value[:-1]}+00:00"
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        try:
            return parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return None


def fmt_date(value: datetime | None) -> str:
    if not value:
        return "n/a"
    return value.astimezone(timezone.utc).strftime("%b %d, %Y")


def badge(label: str, value: str, color: str = "0f766e") -> str:
    clean_label = urllib.parse.quote(label.replace("-", "--").replace("_", "__"), safe="")
    clean_value = urllib.parse.quote(value.replace("-", "--").replace("_", "__"), safe="")
    return f"![{label}: {value}](https://img.shields.io/badge/{clean_label}-{clean_value}-{color}?style=flat-square)"


def status_badge(product: dict[str, Any]) -> str:
    label = urllib.parse.quote(product["status"], safe="")
    return (
        f'<img alt="{product["status"]}" '
        f'src="https://img.shields.io/badge/{label}-{product["status_color"]}?style=flat-square&labelColor=111827">'
    )


def product_key(product: dict[str, Any]) -> str:
    return product.get("short_name") or product["name"]


def repo_matches(product: dict[str, Any], full_name: str) -> bool:
    normalized = full_name.lower()
    return any(re.search(pattern, normalized) for pattern in product["match"])


def fetch_accessible_repos(token: str) -> list[dict[str, Any]]:
    repos: dict[str, dict[str, Any]] = {}
    sources = [
        f"/users/{GITHUB_USER}/repos?per_page=100&type=owner&sort=updated",
        f"/orgs/{ORG}/repos?per_page=100&type=all&sort=updated",
    ]
    for source in sources:
        try:
            for repo in api_pages(source, token):
                repos[repo["full_name"]] = repo
        except GitHubError as exc:
            if exc.status in {401, 403, 404}:
                continue
            raise
    return list(repos.values())


def fetch_repo_details(full_name: str, token: str) -> dict[str, Any] | None:
    try:
        repo = api_json(f"/repos/{full_name}", token)
    except GitHubError as exc:
        if exc.status in {401, 403, 404}:
            return None
        raise

    try:
        languages = api_json(repo["languages_url"], token) or {}
    except GitHubError:
        languages = {}

    user_commits = 0
    try:
        contributors = api_json(f"/repos/{full_name}/contributors?per_page=100&anon=false", token) or []
        if isinstance(contributors, list):
            for contributor in contributors:
                if contributor.get("login") == GITHUB_USER:
                    user_commits += int(contributor.get("contributions") or 0)
    except GitHubError:
        user_commits = 0

    return {
        "full_name": repo["full_name"],
        "html_url": repo["html_url"],
        "private": bool(repo.get("private")),
        "stars": int(repo.get("stargazers_count") or 0),
        "forks": int(repo.get("forks_count") or 0),
        "updated_at": parse_dt(repo.get("updated_at")),
        "pushed_at": parse_dt(repo.get("pushed_at")),
        "language": repo.get("language") or "Other",
        "languages": languages,
        "user_commits": user_commits,
    }


def collect(token: str) -> tuple[dict[str, list[dict[str, Any]]], list[str]]:
    repos = fetch_accessible_repos(token)
    matched_names: dict[str, set[str]] = defaultdict(set)

    for repo in repos:
        full_name = repo["full_name"]
        for product in PRODUCTS:
            if repo_matches(product, full_name):
                matched_names[product_key(product)].add(full_name)

    by_product: dict[str, list[dict[str, Any]]] = defaultdict(list)
    inaccessible: list[str] = []
    for product in PRODUCTS:
        key = product_key(product)
        for full_name in sorted(matched_names[key]):
            details = fetch_repo_details(full_name, token)
            if details:
                by_product[key].append(details)
            else:
                inaccessible.append(full_name)

    return by_product, inaccessible


def aggregate_language_bytes(repos: list[dict[str, Any]]) -> Counter[str]:
    language_bytes: Counter[str] = Counter()
    for repo in repos:
        for language, byte_count in repo["languages"].items():
            language_bytes[language] += int(byte_count)
        if not repo["languages"] and repo["language"] != "Other":
            language_bytes[repo["language"]] += 1
    return language_bytes


def repo_latest(repo: dict[str, Any]) -> datetime | None:
    return max(filter(None, [repo["updated_at"], repo["pushed_at"]]), default=None)


def product_summary(product: dict[str, Any], repos: list[dict[str, Any]]) -> str:
    if not repos:
        return "No tracked repos yet"
    latest = max((repo_latest(repo) for repo in repos), default=None)
    private = sum(1 for repo in repos if repo["private"])
    languages = ", ".join(lang for lang, _ in aggregate_language_bytes(repos).most_common(3)) or "Mixed"
    repo_word = "repo" if len(repos) == 1 else "repos"
    return f"{len(repos)} {repo_word} · {private} private · {languages} · updated {fmt_date(latest)}"


def render_apps(by_product: dict[str, list[dict[str, Any]]]) -> str:
    lines = [
        BLOCKS["apps"][0],
        "<!-- Generated by .github/scripts/update_profile_stats.py -->",
        "",
    ]

    for index, product in enumerate(PRODUCTS):
        key = product_key(product)
        repos = by_product.get(key, [])
        tag_line = " · ".join(product["tags"])
        links = " · ".join(f'<a href="{url}">{label}</a>' for label, url in product["links"])
        lines.extend(
            [
                f'<p>',
                f'  <img align="left" width="58" height="58" src="{product["icon"]}" alt="{product["name"]} icon" />',
                f'  <strong>{product["emoji"]} {product["name"]}</strong> {status_badge(product)}<br>',
                f'  <strong>Stack:</strong> {tag_line}<br>',
                f'  {product["summary"]}<br>',
                f'  <sub>{product_summary(product, repos)}</sub><br>',
                f'  {links}',
                f'</p>',
                '<br clear="left" />',
            ]
        )
        if index != len(PRODUCTS) - 1:
            lines.extend(["", "---", ""])

    lines.append(BLOCKS["apps"][1])
    return "\n".join(lines)


def render_courses() -> str:
    lines = [
        BLOCKS["courses"][0],
        "<!-- Generated by .github/scripts/update_profile_stats.py -->",
        "",
    ]
    for course in COURSES:
        lines.append(
            f'- <img width="20" src="{course["icon"]}" alt="" /> '
            f'[{course["name"]}]({course["url"]}) — {course["topic"]}'
        )
    lines.extend(["", BLOCKS["courses"][1]])
    return "\n".join(lines)


def render_stats(by_product: dict[str, list[dict[str, Any]]]) -> str:
    repos = [repo for product_repos in by_product.values() for repo in product_repos]
    language_bytes = aggregate_language_bytes(repos)
    latest = max((repo_latest(repo) for repo in repos), default=None)
    total_private = sum(1 for repo in repos if repo["private"])
    total_public = len(repos) - total_private
    total_stars = sum(repo["stars"] for repo in repos)
    total_forks = sum(repo["forks"] for repo in repos)
    total_commits = sum(repo["user_commits"] for repo in repos)

    total_bytes = max(sum(language_bytes.values()), 1)
    language_text = " · ".join(
        f"**{language}** {round(byte_count / total_bytes * 100):.0f}%"
        for language, byte_count in language_bytes.most_common(6)
    )

    badges = " ".join(
        [
            badge("tracked repos", str(len(repos))),
            badge("private", str(total_private), "7c3aed"),
            badge("public", str(total_public), "0369a1"),
            badge("stars", str(total_stars), "ca8a04"),
            badge("forks", str(total_forks), "64748b"),
            badge("tracked commits", str(total_commits), "be123c"),
        ]
    )

    lines = [
        BLOCKS["stats"][0],
        "<!-- Generated by .github/scripts/update_profile_stats.py -->",
        "",
        badges,
        "",
        f"**Stack mix:** {language_text}",
        "",
        "**Product pulse:**",
    ]

    for product in PRODUCTS:
        key = product_key(product)
        repos_for_product = by_product.get(key, [])
        if not repos_for_product:
            continue
        lines.append(f"- {product['emoji']} **{product['name']}** — {product_summary(product, repos_for_product)}")

    lines.extend(["", f"_Latest tracked repo update: {fmt_date(latest)}._", BLOCKS["stats"][1]])
    return "\n".join(lines)


def render_activity(by_product: dict[str, list[dict[str, Any]]]) -> str:
    repos = [repo for product_repos in by_product.values() for repo in product_repos]
    repos.sort(key=lambda repo: repo_latest(repo) or datetime.min.replace(tzinfo=timezone.utc), reverse=True)

    lines = [
        BLOCKS["activity"][0],
        "<!-- Generated by .github/scripts/update_profile_stats.py -->",
        "",
    ]

    for repo in repos[:10]:
        private_label = "private" if repo["private"] else "public"
        latest = fmt_date(repo_latest(repo))
        if repo["private"]:
            repo_label = f"**{repo['full_name']}**"
        else:
            repo_label = f"**[{repo['full_name']}]({repo['html_url']})**"
        lines.append(f"- 🛠️ {repo_label} · {private_label} · updated {latest}")

    lines.extend(["", BLOCKS["activity"][1]])
    return "\n".join(lines)


def replace_block(readme: str, block_name: str, rendered: str) -> str:
    start, end = BLOCKS[block_name]
    pattern = re.compile(rf"{re.escape(start)}.*?{re.escape(end)}", re.DOTALL)
    if not pattern.search(readme):
        raise RuntimeError(f"README.md must contain {start} and {end}")
    return pattern.sub(rendered, readme, count=1)


def main() -> int:
    if not has_private_token():
        print("PROFILE_STATS_TOKEN is not configured. Leaving generated README sections unchanged.")
        return 0

    token = github_token()
    readme = open(README_PATH, "r", encoding="utf-8").read()
    by_product, inaccessible = collect(token)

    if inaccessible and os.environ.get("PROFILE_STATS_TOKEN"):
        raise RuntimeError("Could not access tracked private repos: " + ", ".join(inaccessible))
    if inaccessible and not token:
        print("Private repositories are not accessible. Leaving README unchanged until PROFILE_STATS_TOKEN is configured.")
        return 0

    updated = readme
    updated = replace_block(updated, "apps", render_apps(by_product))
    updated = replace_block(updated, "courses", render_courses())
    updated = replace_block(updated, "stats", render_stats(by_product))
    updated = replace_block(updated, "activity", render_activity(by_product))

    if updated != readme:
        open(README_PATH, "w", encoding="utf-8").write(updated)
        print("Updated generated README sections.")
    else:
        print("README generated sections already up to date.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
