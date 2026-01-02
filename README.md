# The Next Step

> "The most important step a man can take. It's not the first one, is it? It's the next one. Always the next step, Dalinar."
>
> — Dalinar Kholin, *Oathbringer*

An AI-assisted task suggestion service for neurodivergent individuals to move from uncertainty to action, reducing decision paralysis and cognitive burden.

## Overview

**The Next Step** helps neurodivergent adults (ADHD, autism, and others) execute tasks aligned with their values by:

- **Reducing cognitive burden:** AI suggests a single next task, not an overwhelming list
- **Respecting agency:** Users decide; the system only nudges
- **Fuzzy suggestion algorithm:** Prevents nagging the same task; learns from rejection to suggest alternatives
- **Value alignment:** Tasks connected to personal values; progress shown by value, not productivity metrics
- **Multi-platform:** Web interface for planning, mobile for quick "what next?" suggestions

## Project Structure

```
the-next-step/
├── backend/          # Python + FastAPI + SQLAlchemy + PostgreSQL
├── web/              # React + TypeScript + Vite
├── mobile/           # React Native + TypeScript
├── shared/           # TypeScript: API client, shared types
├── docs/             # Architecture docs, API reference, design docs
├── .github/          # GitHub Actions CI/CD workflows
└── MVP_Requirements.md  # Full product specification
```

## Quick Start

### Prerequisites

- Python 3.11+ (with `uv` package manager)
- Node.js 18+ (with npm)
- PostgreSQL 14+ (or Docker for local development)

### Backend Setup

```bash
cd backend
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

### Web Frontend Setup

```bash
cd web
npm install
npm run dev
```

### Mobile Frontend Setup

```bash
cd mobile
npm install
npm start
```

## Development Workflow

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed local setup and testing.

## Product Specification

See [MVP_Requirements.md](MVP_Requirements.md) for the full product specification, including:
- Task model and states
- Values system
- Morning planning and "what next?" flows
- Evening review with modular cards
- Scoring algorithm and dampening logic

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for technical design decisions.

## Developer Context

This is a **learning project** focused on GitHub workflows and GitHub Copilot development patterns. Built by a developer with 12 years professional experience in Java and Groovy.

**Tech stack chosen for Copilot compatibility:** Python/FastAPI (backend), React/TypeScript (web), React Native (mobile)

The primary goal is learning to work effectively with GitHub and Copilot, not mastering these specific languages. If contributing or reviewing code, explanations of Python/JS/TS patterns are helpful - JVM comparisons appreciated when relevant!

## Contributing

This is a solo learning project, but the codebase is public. Feel free to explore, fork, or adapt for your own use.

## License

MIT (or your choice)

## Next Steps (For Development)

- [ ] Create GitHub repository
- [ ] Configure PostgreSQL (local or Docker)
- [ ] Set up GitHub Actions CI/CD
- [ ] Build backend API scaffolds
- [ ] Build web UI scaffolds
- [ ] Build mobile UI scaffolds
- [ ] Implement task CRUD endpoints
- [ ] Implement scoring algorithm
- [ ] Connect frontends to API
