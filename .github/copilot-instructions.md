# GitHub Copilot Instructions

## Developer Background

**Primary experience:** 12 years professional experience in Java and Groovy
**Current focus:** Learning GitHub workflows and GitHub Copilot development patterns
**Language choice:** Python/JS/TS chosen for this project because they work well with Copilot, not due to prior expertise
**Strengths:** Backend architecture, database design, general software engineering patterns
**Needs help with:** Python/JS/TS idioms, ecosystem conventions, library-specific patterns

## Communication Preferences

- **Explain patterns from first principles** - Don't assume familiarity with Python/JS/TS idioms
- **Compare to JVM equivalents when useful** - e.g., "This is like Spring's dependency injection" or "Similar to JUnit fixtures"
- **Explain library-specific patterns** - FastAPI, React, SQLAlchemy conventions may not be obvious
- **Be explicit about ecosystem tools** - uvicorn, pytest, vite, npm conventions need explanation

## Code Review Focus

When reviewing or generating code, please:
- Explain **why** certain patterns are used (not just what)
- Point out **Python/JS/TS idioms** that differ from JVM conventions
- Call out **ecosystem-specific conventions** (e.g., FastAPI dependency injection, React hooks)
- Suggest **better patterns** if I'm using JVM approaches where Python/JS/TS has better solutions

## Project Context

This is a **learning project** focused on:
- GitHub workflows (issues, PRs, reviews, CI/CD)
- GitHub Copilot development patterns (CLI, web UI, code generation)
- Modern full-stack development with AI assistance
- Technologies: FastAPI/SQLAlchemy (backend), React/TypeScript (web), React Native (mobile)

The goal is understanding **GitHub + Copilot workflows**, not mastering Python/JS/TS. These languages were chosen because they work well with Copilot.

## Development Practices

### Test-Driven Development (TDD)
- **Prefer TDD approach when feasible** - write tests before implementation
- Tests help clarify requirements and prevent regressions
- For new features:
  1. Write failing test that describes desired behavior
  2. Implement minimal code to make test pass
  3. Refactor while keeping tests green
- For bug fixes: Write test that reproduces the bug, then fix it
- Backend: Use pytest with fixtures and FastAPI TestClient
- Frontend: Testing approach TBD (manual verification acceptable initially)

### CI/CD Requirements

**Before considering any work complete:**
- Run `./scripts/check-ci.sh` to validate all checks pass locally
- **NEVER** push code that fails CI checks - validate locally first
- **NEVER** merge PRs (including sub-PRs) without green CI checks
- Do not rely on GitHub Actions to catch failures - validate locally first
- This includes: backend tests, web tests, type checking, linting, builds

**For sub-PRs targeting feature branches:**
- Sub-PRs targeting feature branches MUST run CI checks locally before merging
- Use `./scripts/check-ci.sh` to validate before creating PR
- Even if GitHub Actions doesn't auto-run, you are responsible for validation
- The feature branch PR will catch issues, but that's too late - catch them early

**Quick check command:**
```bash
./scripts/check-ci.sh
```

## Technical Debt Policy

When encountering technical debt during code review, development, or CI/CD work:

**Automatically create a GitHub issue** if the debt meets these criteria:
- **Unrelated to current task** - Don't mix feature work with tech debt fixes
- **Clearly scoped and actionable** - Specific file/line numbers, clear fix
- **Not a blocking issue** - Tests pass, feature works, but improvement is needed

**Issue format:**
```markdown
## Description
Brief summary of the technical debt

## Context
- Where/when discovered (PR, issue, or task)
- Why it exists (if known)
- Impact: tests pass but type safety/linting/deprecation warnings

## Issues to Fix
Specific problems with:
- File and line numbers
- Current code (show the problem)
- Proposed solution (show the fix)

## Acceptance Criteria
- [ ] Checklist of fixes
- [ ] All tests still pass
- [ ] Linting/type checking passes
- [ ] CI/CD passes

## Technical Notes
Context for the developer (JVM analogies if helpful)
```

**Examples of tech debt to auto-create issues for:**
- Type checking errors (pyright, TypeScript strict mode)
- Linting warnings that should be fixed
- Deprecation warnings for libraries/APIs
- Missing null checks or error handling
- Code duplication that should be refactored

**Don't create issues for:**
- Blocking bugs or test failures (fix immediately)
- Simple typos or formatting (fix inline)
- Architectural decisions that need discussion (ask first)

**Labels to use:**
- `technical-debt` (primary)
- Area: `backend`, `frontend`, `mobile`, `ci-cd`
- Type: `type-safety`, `testing`, `refactoring`, `deprecation`

## Example Helpful Explanations

✅ Good: "We use `app.dependency_overrides` to mock FastAPI dependencies in tests - this is similar to Spring's `@MockBean` but works through FastAPI's dependency injection system"

❌ Less helpful: "Just use `app.dependency_overrides` here"

✅ Good: "In Python, we use `pytest` fixtures (like JUnit's `@Before`) but they're more powerful - they can be scoped per function/class/module and have automatic cleanup"

❌ Less helpful: "Add a pytest fixture"
