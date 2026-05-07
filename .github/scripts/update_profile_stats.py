#!/usr/bin/env python3
"""Update the generated portfolio stats block in README.md."""

from __future__ import annotations

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
START = "<!-- PROFILE-STATS:START -->"
END = "<!-- PROFILE-STATS:END -->"
GITHUB_USER = "chochy2001"
API_ROOT = "https://api.github.com"

PROJECTS = [
    {
        "name": "Capdesis",
        "summary": "Company sites, product operations, and shared platform work.",
        "repos": [
            "CAPDESIS/CapdesisWebLanding",
            "CAPDESIS/CapdesisWeb",
        ],
    },
    {
        "name": "Ingenieria Tracker",
        "summary": "Academic planning and engineering student tools across apps, backend, and data.",
        "repos": [
            "CAPDESIS/IngenieriaTracker-Meta",
            "CAPDESIS/IngenieriaTrackerFree",
            "CAPDESIS/IngenieriaTrackerPro",
            "CAPDESIS/IngeTrackerBackend",
            "CAPDESIS/BasesDatosIngenieriaTracker",
        ],
    },
    {
        "name": "Formulae",
        "summary": "Math and science learning apps, public site, and store builds.",
        "repos": [
            "CAPDESIS/formulaeapps",
            "CAPDESIS/FormulaePro",
            "CAPDESIS/FormulaeCommunity",
        ],
    },
    {
        "name": "Capmenu",
        "summary": "Digital restaurant platform across Flutter, backend, web, and deployment work.",
        "repos": [
            "CAPDESIS/CapmenuApps",
            "CAPDESIS/MenuRestaurante",
            "CAPDESIS/CapmenuBack",
            "CAPDESIS/CapmenuBackend",
            "CAPDESIS/CapmenuFlutterFrontendWeb",
            "CAPDESIS/CapmenuProject",
        ],
    },
    {
        "name": "Cap Living",
        "summary": "Housing and property operations product work.",
        "repos": [
            "CAPDESIS/CapLiving",
        ],
    },
    {
        "name": "Lo Mas Fresh",
        "summary": "Fresh produce marketplace and provider operations.",
        "repos": [
            "CAPDESIS/lo_mas_fresh",
        ],
    },
    {
        "name": "CapTienda",
        "summary": "Point of sale, retail operations, backend, and landing work.",
        "repos": [
            "CAPDESIS/pos_tienda",
            "CAPDESIS/capdesis_pos_backend",
            "CAPDESIS/captienda_landing",
        ],
    },
    {
        "name": "OmniMon",
        "summary": "Cross-platform system monitoring, landing page, package distribution, and private app work.",
        "repos": [
            "chochy2001/omnimon",
            "chochy2001/omnimon_landing",
            "chochy2001/homebrew-omnimon",
            "CAPDESIS/omnimon_apps",
        ],
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


def api_json(path_or_url: str, token: str) -> Any:
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
            if not data:
                return None
            import json

            return json.loads(data)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise GitHubError(url, exc.code, body[:240]) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"{url} failed: {exc.reason}") from exc


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


def fetch_repo(full_name: str, token: str) -> dict[str, Any]:
    repo = api_json(f"/repos/{full_name}", token)
    languages = {}
    contributors = []

    try:
        languages = api_json(repo["languages_url"], token) or {}
    except GitHubError:
        languages = {}

    try:
        contributors = api_json(f"/repos/{full_name}/contributors?per_page=100&anon=false", token) or []
    except GitHubError as exc:
        if exc.status != 202:
            contributors = []

    user_commits = 0
    if isinstance(contributors, list):
        for contributor in contributors:
            if contributor.get("login") == GITHUB_USER:
                user_commits += int(contributor.get("contributions") or 0)

    return {
        "full_name": repo["full_name"],
        "html_url": repo["html_url"],
        "private": bool(repo.get("private")),
        "stars": int(repo.get("stargazers_count") or 0),
        "forks": int(repo.get("forks_count") or 0),
        "open_issues": int(repo.get("open_issues_count") or 0),
        "updated_at": parse_dt(repo.get("updated_at")),
        "pushed_at": parse_dt(repo.get("pushed_at")),
        "language": (repo.get("language") or "Other"),
        "languages": languages,
        "user_commits": user_commits,
    }


def collect(token: str) -> tuple[dict[str, list[dict[str, Any]]], list[str]]:
    by_project: dict[str, list[dict[str, Any]]] = defaultdict(list)
    inaccessible: list[str] = []

    for project in PROJECTS:
        for full_name in project["repos"]:
            try:
                by_project[project["name"]].append(fetch_repo(full_name, token))
            except GitHubError as exc:
                if exc.status in {401, 403, 404}:
                    inaccessible.append(full_name)
                    continue
                raise

    return by_project, inaccessible


def project_rows(by_project: dict[str, list[dict[str, Any]]]) -> list[str]:
    rows = [
        "| Area | Tracked repos | Stack signal | Latest update | What it represents |",
        "| --- | ---: | --- | --- | --- |",
    ]

    summaries = {project["name"]: project["summary"] for project in PROJECTS}
    for project in PROJECTS:
        name = project["name"]
        repos = by_project.get(name, [])
        language_bytes: Counter[str] = Counter()
        latest = None
        private_count = 0
        for repo in repos:
            private_count += 1 if repo["private"] else 0
            latest = max(filter(None, [latest, repo["updated_at"], repo["pushed_at"]]), default=latest)
            for language, byte_count in repo["languages"].items():
                language_bytes[language] += int(byte_count)
            if not repo["languages"] and repo["language"] != "Other":
                language_bytes[repo["language"]] += 1

        languages = ", ".join(language for language, _ in language_bytes.most_common(4)) or "Mixed"
        privacy = f"{private_count} private" if private_count else "public"
        tracked = f"{len(repos)} ({privacy})" if repos else "0"
        rows.append(
            f"| **{name}** | {tracked} | {languages} | {fmt_date(latest)} | {summaries[name]} |"
        )

    return rows


def render(by_project: dict[str, list[dict[str, Any]]]) -> str:
    repos = [repo for project_repos in by_project.values() for repo in project_repos]
    language_bytes: Counter[str] = Counter()
    latest = None

    for repo in repos:
        latest = max(filter(None, [latest, repo["updated_at"], repo["pushed_at"]]), default=latest)
        for language, byte_count in repo["languages"].items():
            language_bytes[language] += int(byte_count)
        if not repo["languages"] and repo["language"] != "Other":
            language_bytes[repo["language"]] += 1

    total_private = sum(1 for repo in repos if repo["private"])
    total_public = len(repos) - total_private
    total_stars = sum(repo["stars"] for repo in repos)
    total_forks = sum(repo["forks"] for repo in repos)
    total_commits = sum(repo["user_commits"] for repo in repos)

    language_badges = " ".join(
        badge(language, f"{round(bytes_count / max(sum(language_bytes.values()), 1) * 100):.0f}%", "2563eb")
        for language, bytes_count in language_bytes.most_common(6)
    )

    summary_badges = " ".join(
        [
            badge("tracked repos", str(len(repos))),
            badge("private", str(total_private), "7c3aed"),
            badge("public", str(total_public), "0369a1"),
            badge("stars", str(total_stars), "ca8a04"),
            badge("forks", str(total_forks), "64748b"),
        ]
    )
    if total_commits:
        summary_badges += " " + badge("tracked commits", str(total_commits), "be123c")

    lines = [
        START,
        "<!-- This block is generated by .github/scripts/update_profile_stats.py. -->",
        "",
        summary_badges,
        "",
        language_badges,
        "",
        "\n".join(project_rows(by_project)),
        "",
        f"_Latest tracked repo update: {fmt_date(latest)}._",
        END,
    ]
    return "\n".join(lines)


def replace_block(readme: str, block: str) -> str:
    pattern = re.compile(rf"{re.escape(START)}.*?{re.escape(END)}", re.DOTALL)
    if not pattern.search(readme):
        raise RuntimeError(f"README.md must contain {START} and {END}")
    return pattern.sub(block, readme, count=1)


def main() -> int:
    token = github_token()
    readme = open(README_PATH, "r", encoding="utf-8").read()
    by_project, inaccessible = collect(token)

    if inaccessible:
        profile_token_configured = bool(os.environ.get("PROFILE_STATS_TOKEN"))
        message = "Could not access tracked private repos: " + ", ".join(inaccessible)
        if profile_token_configured:
            raise RuntimeError(message)
        print(f"{message}. Leaving README stats unchanged until PROFILE_STATS_TOKEN is configured.")
        return 0

    updated = replace_block(readme, render(by_project))
    if updated != readme:
        open(README_PATH, "w", encoding="utf-8").write(updated)
        print("Updated README profile stats.")
    else:
        print("README profile stats already up to date.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
