# Development Scripts

## check-ci.sh

Runs all CI checks locally before pushing code.

**Usage:**
```bash
./scripts/check-ci.sh
```

**What it checks:**
- **Backend:**
  - Ruff linting (`ruff check`)
  - Ruff formatting (`ruff format --check`)
  - Pyright type checking
  - Pytest tests
- **Web:**
  - TypeScript type checking
  - ESLint linting
  - Build validation

**When to run:**
- Before creating a PR
- Before merging a sub-PR
- After making changes that might affect CI
- When GitHub Actions fails (to reproduce locally)

**Pro tip:** Add this to your git pre-push hook to automate the check:
```bash
# .git/hooks/pre-push
#!/bin/bash
./scripts/check-ci.sh
```
