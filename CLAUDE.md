# CLAUDE.md

<!-- CAPDESIS INFRA START -->
## CAPDESIS Architecture And Delivery Policy

This repo participates in the shared CAPDESIS workspace architecture. Keep this
block aligned with the canonical local docs under
`/Users/jorge/Documents/Apps/docs/`:

- `TAILSKILL_NEW_VPS_HANDOFF.md`: current VPS, Tailscale, CI runner,
  production, storage, and rollback topology.
- `STAGING_RELEASE_POLICY.md`: legacy filename; direct production release gates,
  plus the verified 2026-09-17 state of the GitHub plan and the disabled deploys.
- `PRODUCTION_ALERTING_RUNBOOK.md`: centralized monitoring and alert routing.
- `APP_RELEASE_READINESS_AUDIT.md`: app deploy workflow state and remaining
  production gaps.
- `SCALING_AND_LOAD_TEST_PLAN.md`: production-safe load testing and scaling
  decision rules.
- `INFRASTRUCTURE_COSTS.md`: verified VPS cost baseline and annual estimates.

Current operating model:

- Linux CI/CD runs on `ci-runner-node` (`vmi3166182`, public
  `185.237.252.45`, Tailscale `100.120.6.51`) using explicit GitHub Actions
  labels such as `[self-hosted, ci-runner-node, test-light]`,
  `[self-hosted, ci-runner-node, build-heavy]`, and
  `[self-hosted, ci-runner-node, deploy-only]`.
- **Staging is not a deploy target (verified 2026-09-17).** `staging-node`
  (`vmi2875906`, Tailscale `100.97.107.71`) is still reachable, but it has **no
  GitHub Actions runner registered** and **no workflow in this repo references
  it**. Do not describe a staging deploy, a staging SHA, or staging smoke/load
  validation as part of this repo's delivery path.
- Production stays on `web-app-proxy` / `ancare` (`100.77.243.93`) with the
  shared Traefik edge, production Docker stacks, runtime volumes, and customer
  traffic.
- Databases stay private on `db-architecture` (`100.88.85.128`). Backups and
  storage validation live on `storage-backups` (`100.120.133.78`) and
  `capdesis-nas` (`100.124.183.32`).
- **Production promotion (policy 2026-07-22, still in force).** Promotion is
  manual, from an exact CI-green `main` SHA, straight to production. The old
  Monday-only window and the "last known-good staging SHA" rule are retired.
  Failed CI, failed health checks, failed smoke/load thresholds, missing backups
  for data-changing releases, unresolved P0/P1 alerts, or unavailable monitoring
  all block promotion; there is no emergency bypass.
- **GitHub plan reality (verified 2026-09-17).** The CAPDESIS org is on the
  GitHub **Free** plan, so there are no required status checks, no branch
  protection and no rulesets on private repos, and GitHub Advanced Security is
  off. "CI passed" is never enforced by the platform; verify it yourself.
- Production alerts should converge in `monitor.capdesis.com` /
  Alertmanager/Grafana. Open P0/P1 alerts block promotion.
- Do not move Traefik, production databases, production secrets, or runtime
  production volumes onto `ci-runner-node` or `staging-node` without a
  separate migration plan and validation evidence.

Before changing deploy behavior in this repo, verify the current workflow
labels, production target, secrets scope, and rollback path
against the canonical docs above.
<!-- CAPDESIS INFRA END -->
