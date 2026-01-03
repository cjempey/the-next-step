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

---

## Guidelines for Working with GitHub Copilot Coding Agent

### Issue Guidelines

When creating issues for Copilot to work on, follow these best practices:

**Well-Scoped Issues:**
- Clearly specify the problem or requested feature
- Define acceptance criteria (should there be tests? what makes a solution "good"?)
- Specify which files or parts of the codebase need to be changed
- Provide relevant context and constraints
- Well-written issues work as strong AI prompts for Copilot

**Example Good Issue:**
```markdown
## Problem
The API returns 500 errors when a user tries to fetch tasks without being authenticated.

## Expected Behavior
- Return 401 Unauthorized with a clear error message
- Include WWW-Authenticate header

## Files to Change
- backend/app/api/tasks.py
- backend/tests/test_tasks.py (add test case)

## Acceptance Criteria
- [ ] Returns 401 status code for unauthenticated requests
- [ ] Includes WWW-Authenticate header
- [ ] Test case added and passing
- [ ] CI/CD passes
```

### Task Selection Guidelines

**Good Tasks for Copilot** (routine, well-defined, low-to-medium complexity):
- Fixing bugs with clear reproduction steps
- Refactoring code (renaming, extracting functions, improving structure)
- Incremental feature improvements
- Improving documentation or test coverage
- Addressing technical debt with clear scope
- Adding logging or error handling
- Updating dependencies (with security checks)

**Tasks to Handle Yourself** (require human judgment):
- Ambiguous requirements needing stakeholder clarification
- Business-critical features with high-stakes consequences
- Deep domain knowledge or architectural decisions
- Heavy cross-repository changes
- Security-sensitive operations beyond standard practices
- Performance optimizations requiring profiling and analysis

### Code Review and Iteration Workflow

**Treat Copilot as a Collaborator:**
- Always review all pull requests before merging
- Use PR comments to guide improvements - you can @mention @copilot in PR comments
- Iterate until the solution meets quality standards
- Don't merge incomplete or low-quality solutions just because they were AI-generated

**Effective PR Review Comments:**
- Be specific about what needs to change
- Provide examples when possible
- Reference coding standards or existing patterns
- Ask questions to clarify intent

**Example PR Comments:**
```markdown
@copilot The error handling here doesn't follow our pattern. Please:
1. Use the `handle_api_error` helper from `app/utils/errors.py`
2. Log the error with context before returning the response
3. Add a test case for this error scenario
```

### Repository Structure and Context

**Project Overview:**
- Full-stack application with backend (FastAPI/Python), web (React/TypeScript), and mobile (React Native)
- Focus on task management with AI-driven suggestions
- Target users: neurodivergent individuals needing reduced cognitive burden

**Key Directories:**
- `backend/` - Python FastAPI application with SQLAlchemy ORM
- `web/` - React TypeScript application with Vite build
- `mobile/` - React Native TypeScript application
- `docs/` - Architecture and design documentation
- `scripts/` - Development and CI/CD helper scripts

**Important Files:**
- `MVP_Requirements.md` - Product specification and features
- `scripts/check-ci.sh` - Local CI validation script
- `.github/workflows/ci.yml` - CI/CD pipeline configuration

**Development Commands:**
- Backend: `cd backend && uv pip install -r requirements.txt && pytest`
- Web: `cd web && npm install && npm run dev`
- Full CI Check: `./scripts/check-ci.sh`

**Code Organization Patterns:**
- Backend: Follow FastAPI's dependency injection pattern
- Testing: pytest for backend, Jest/React Testing Library for web (TBD)
- Type Safety: Use pyright for Python, TypeScript strict mode for frontend
- Error Handling: Centralized error handlers in backend, consistent error responses

### Branch and PR Conventions

**Branch Naming:**
- Copilot automatically creates branches with `copilot/` prefix
- Feature branches: `feature/description`
- Bug fixes: `fix/description`
- Documentation: `docs/description`

**PR Guidelines:**
- All PRs must pass CI/CD before merging
- Sub-PRs to feature branches must validate CI locally
- Include clear description of changes and why they were made
- Link to related issues
- Request review from @cjempey for architectural or business logic questions

### Security and Quality Standards

**Before Merging:**
- All tests pass locally and in CI
- No linting or type checking errors
- Code follows existing patterns and conventions
- Security vulnerabilities addressed (Copilot runs security checks)
- No sensitive data or secrets in code

**When Copilot Identifies Issues:**
- Review security alerts carefully
- Fix vulnerabilities in code you're changing
- Create issues for unrelated vulnerabilities (don't expand scope)
- Document decisions if choosing to defer a fix
