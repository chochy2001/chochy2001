# CLAUDE.md

## Overview

`chochy2001/chochy2001` is the **public** GitHub profile repository for Jorge Salgado Miranda (`README.md` rendered on `https://github.com/chochy2001`).

## Repository Layout & Automation

- `README.md`: Profile overview and bounded auto-generated marker blocks (`COURSES`, `APPS`, `PROFILE-STATS`, `PRIVATE-ACTIVITY`, `YOUTUBE`). Edit static copy outside marker pairs; keep marker comments intact so scheduled workflows can update generated sections cleanly.
- `.github/scripts/update_profile_stats.py`: Python 3 standard-library generator that refreshes `COURSES`, `APPS`, `PROFILE-STATS`, and `PRIVATE-ACTIVITY` in `README.md`. Validate script changes locally with `python3 -m py_compile .github/scripts/update_profile_stats.py`.
- `.github/workflows/update-readme.yml`: Runs `update_profile_stats.py` on GitHub-hosted `ubuntu-latest` (`schedule`, `push` to `main`, `workflow_dispatch`, and `repository_dispatch`) and commits `README.md` updates when content changes.
- `.github/workflows/youtube-workflow.yml`: Refreshes the `YOUTUBE` feed block in `README.md` on GitHub-hosted `ubuntu-latest`.

## Local Workspace & Public Hygiene Rules

- **Public repository boundary:** Every commit and file in this repository is world-readable. Never commit secrets, tokens, internal hostnames, public or private/Tailscale IP addresses, internal runbooks, or local machine paths here.
- **Nested local checkouts:** Local developer workspaces may place sibling repositories (`agent-fleet/` and `opencampus-data/`) inside the local `chochy2001/` directory. Both paths are ignored via `.gitignore` and must **never** be staged, committed, or added as Git submodules / gitlinks.
- **Workspace instructions:** When working from a multi-repository local workspace, defer to the workspace-level `AGENTS.md` for cross-repo conventions and tooling rather than embedding internal infrastructure or operational policy in this public repository.
