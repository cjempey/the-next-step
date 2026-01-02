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

## CI/CD Requirements

**Before considering any work complete:**
- Run all CI checks locally to ensure they pass
- Verify linting, type checking, tests, and builds succeed
- Do not rely on GitHub Actions to catch failures - validate locally first
- This includes: backend tests, web tests, type checking, linting, etc.

## Example Helpful Explanations

✅ Good: "We use `app.dependency_overrides` to mock FastAPI dependencies in tests - this is similar to Spring's `@MockBean` but works through FastAPI's dependency injection system"

❌ Less helpful: "Just use `app.dependency_overrides` here"

✅ Good: "In Python, we use `pytest` fixtures (like JUnit's `@Before`) but they're more powerful - they can be scoped per function/class/module and have automatic cleanup"

❌ Less helpful: "Add a pytest fixture"
