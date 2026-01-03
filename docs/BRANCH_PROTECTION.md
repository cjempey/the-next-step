# Branch Protection Configuration

This document describes the recommended GitHub repository settings for enforcing CI checks.

## Repository Settings (Manual Configuration)

Navigate to: **Settings → Branches → Branch protection rules**

### Protect `main` Branch

**Required Settings:**
- ✅ Require a pull request before merging
  - ✅ Require approvals: 1 (or 0 for solo development with strict CI)
  - ✅ Dismiss stale pull request approvals when new commits are pushed
- ✅ Require status checks to pass before merging
  - ✅ Require branches to be up to date before merging
  - **Required status checks:**
    - `backend / Backend Tests`
    - `web / Web Frontend Tests`
    - `mobile / Mobile Frontend Build`
- ✅ Require conversation resolution before merging
- ❌ Do not allow bypassing the above settings

**Why these settings:**
- Ensures all CI checks pass before code reaches `main`
- Prevents accidental direct pushes to `main`
- Forces code review workflow
- Keeps `main` always in a deployable state

### Optional: Protect Feature Branches

For stricter workflows, you can protect feature branches:

**Branch name pattern:** `feature/*`

**Required Settings:**
- ✅ Require status checks to pass before merging
  - **Required status checks:**
    - `backend / Backend Tests`
    - `web / Web Frontend Tests`

**Why:**
- Ensures sub-PRs (like `copilot/sub-pr-26 → feature/values-ui`) run CI checks
- Catches issues before they reach the main feature branch
- Adds overhead, so only enable if CI gaps are a recurring problem

## GitHub Actions Configuration

File: `.github/workflows/ci.yml`

**Current trigger configuration:**
```yaml
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: ['**']  # Runs on PRs to ANY branch
```

**Why `branches: ['**']` for PRs:**
- Ensures CI runs on sub-PRs targeting feature branches
- Without this, `copilot/sub-pr-26 → feature/values-ui` wouldn't trigger CI
- Catches lint/test failures before merging sub-PRs

## Local Validation

Even with branch protection, **always validate locally first:**

```bash
./scripts/check-ci.sh
```

This runs the same checks GitHub Actions will run, but faster and before pushing.

## Troubleshooting

**"Why didn't CI run on my PR?"**
- Check if your PR targets a branch other than `main` or `develop`
- With `branches: ['**']`, CI should run on all PRs
- If not, check GitHub Actions logs for errors

**"CI passed but local checks fail?"**
- Ensure your local environment matches CI:
  - Python 3.11+ (check with `python --version`)
  - Node 18+ (check with `node --version`)
  - Latest dependencies (`uv sync`, `npm install`)

**"I need to bypass CI temporarily"**
- For personal development repos, you can disable branch protection temporarily
- For team repos, request admin override only in emergencies
- **Never** merge code with failing CI in production scenarios
