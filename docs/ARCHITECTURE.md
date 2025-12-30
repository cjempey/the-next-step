# Architecture & Design Decisions

## Overview

The Next Step is a full-stack application with:
- **Backend:** Python + FastAPI + SQLAlchemy + PostgreSQL
- **Web Frontend:** React + TypeScript + Vite + Zustand
- **Mobile Frontend:** React Native + Expo + TypeScript

## Architecture Diagram

```
┌─────────────────────────────────┐    ┌──────────────────────────┐
│      React Web (Vite)           │    │   React Native (Expo)    │
│  - Morning Planning             │    │  - What Next?            │
│  - Evening Review               │    │  - Context Recovery      │
│  - Settings                     │    │  - Notifications         │
└────────────────┬────────────────┘    └──────────┬───────────────┘
                 │                                 │
                 └──────────────┬──────────────────┘
                                │
                        ┌───────┴──────────────┐
                        │  Zustand Store      │
                        │  (state management) │
                        └───────┬──────────────┘
                                │
                    ┌───────────┴─────────────┐
                    │   API Client (axios)    │
                    │   REST API calls        │
                    └───────────┬─────────────┘
                                │
                    ┌───────────┴──────────────────┐
                    │   FastAPI Backend           │
                    │  - Task CRUD                │
                    │  - Scoring Algorithm        │
                    │  - Review Card Generation   │
                    │  - OpenAI Integration       │
                    └───────────┬──────────────────┘
                                │
                    ┌───────────┴──────────────────┐
                    │    PostgreSQL Database      │
                    │  - Tasks                    │
                    │  - Values                   │
                    │  - Review History           │
                    │  - Rejection Dampening      │
                    │  - Daily Priorities         │
                    └─────────────────────────────┘
```

## Technology Choices

### Backend: Python + FastAPI

**Why?**
- Your professional background (backend services)
- FastAPI is lightweight, async-capable, and excellent for learning
- SQLAlchemy ORM is industry-standard; Alembic provides database versioning
- Easy integration with OpenAI API

**Key Dependencies:**
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `sqlalchemy` - ORM
- `alembic` - Database migrations
- `pydantic` - Data validation & settings management
- `openai` - Optional AI integration
- `psycopg2` - PostgreSQL adapter

### Frontend: React + TypeScript + Vite

**Why?**
- React is well-supported by Copilot and AI coding assistants
- TypeScript provides type safety for complex state management
- Vite is fast and modern (better DX than Create React App)
- Zustand is lightweight state management (vs Redux complexity)

**Key Dependencies:**
- `react` - UI framework
- `zustand` - State management
- `axios` - HTTP client
- `dnd-kit` - Drag-and-drop for morning planning
- `vite` - Build tool

### Mobile: React Native + Expo

**Why?**
- Code reuse with web (both TypeScript, both React paradigm)
- Expo simplifies mobile development (no native build setup needed for MVP)
- Can share business logic (API client, state store) via `npm` packages

**Key Dependencies:**
- `expo` - Framework for rapid development
- `@react-navigation` - Navigation between screens
- `expo-notifications` - Optional push notifications

### Database: PostgreSQL

**Why?**
- You wanted to learn PostgreSQL
- Better for complex queries (blocking detection, recurrence logic)
- Production-ready
- Alembic migrations make schema changes traceable

**Tables:**
- `tasks` - Task model
- `values` - User-defined values
- `task_value_association` - Many-to-many relationship
- `rejection_dampening` - Track rejected tasks for session
- `daily_priorities` - Track tasks selected for the day
- `review_history` - Journaling/audit trail

## Project Structure

```
the-next-step/
├── backend/                          # Python FastAPI backend
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/              # API endpoints
│   │   │       ├── tasks.py
│   │   │       ├── values.py
│   │   │       ├── suggestions.py
│   │   │       └── reviews.py
│   │   ├── core/
│   │   │   └── database.py           # SQLAlchemy setup
│   │   ├── models.py                 # ORM models
│   │   ├── schemas.py                # Pydantic schemas
│   │   ├── config.py                 # Settings
│   │   └── main.py                   # App factory
│   ├── alembic/                      # Database migrations
│   │   ├── versions/
│   │   └── env.py
│   ├── tests/                        # Unit & integration tests
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── run.py                        # Startup script
│   └── .env.example
│
├── web/                              # React web frontend
│   ├── src/
│   │   ├── api/                      # API client
│   │   ├── components/               # React components
│   │   ├── pages/                    # Page components
│   │   ├── store/                    # Zustand state
│   │   ├── hooks/                    # Custom hooks
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/                       # Static assets
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── package.json
│   └── index.html
│
├── mobile/                           # React Native mobile app
│   ├── src/
│   │   ├── api/                      # API client
│   │   ├── screens/                  # Screen components
│   │   ├── components/               # Reusable components
│   │   ├── navigation/               # Navigation setup
│   │   ├── store/                    # Zustand state
│   │   ├── App.tsx
│   │   └── index.js
│   ├── app.json
│   └── package.json
│
├── shared/                           # Shared TypeScript types/utilities (future)
│   └── package.json
│
├── docs/                             # Documentation
│   ├── ARCHITECTURE.md               # This file
│   ├── DEVELOPMENT.md                # Dev setup
│   ├── API.md                        # API documentation
│   └── DATABASE.md                   # Database schema
│
├── .github/workflows/                # GitHub Actions CI/CD
│   ├── test.yml
│   └── deploy.yml
│
├── .gitignore
├── README.md
└── MVP_Requirements.md               # Product spec
```

## Data Flow

### "What Next?" Suggestion Flow

```
1. Frontend (Web/Mobile)
   └─ User clicks "What Next?"
   └─ Calls POST /api/suggestions/next
   
2. Backend API
   └─ Queries database for Ready tasks
   └─ Applies weighting algorithm:
      - Importance weight
      - Urgency weight
      - Strategic nudge (A3/A4)
      - Rejection dampening
      - Daily priority boost
   └─ Normalizes scores to probabilities
   └─ Randomly selects one candidate (fuzzy, not deterministic)
   └─ Returns TaskResponse with reasoning
   
3. Frontend
   └─ Displays single suggestion: "How about [Task]?"
   └─ User chooses: Start / Not now / Take a break
   
4. Backend (if "Not now")
   └─ Records rejection
   └─ Applies dampening to task
   └─ Next suggestion request gets new candidate
```

### Morning Planning Flow

```
1. Frontend
   └─ User navigates to Morning Planning
   └─ Calls GET /api/tasks (filter Ready/Blocked/Parked)
   └─ Calls GET /api/values
   
2. Backend
   └─ Returns tasks grouped in 4 sections:
      - From yesterday's review (In Progress carryovers)
      - Ready or Unblocked (Blocked/Parked that can be revived)
      - Upcoming due dates (due within 7 days, top 3 by score)
      - Other Ready tasks (remaining pool, ranked by score)
   └─ Includes score breakdown (inputs, formula, reasoning)
   
3. Frontend
   └─ Displays tasks in ranked order
   └─ Web: Drag-and-drop to "Today's Priorities" column
   └─ Mobile: Checkboxes to select priorities
   └─ User saves selection
   
4. Backend
   └─ Records daily priority entry
   └─ Tasks in priority list get +2x multiplier for today's "what next" suggestions
   └─ Multiplier expires at evening review
```

### Evening Review Flow

```
1. Frontend
   └─ User initiates Evening Review (or prompted by timer)
   
2. Backend
   └─ Queries tasks completed/in-progress/blocked today
   └─ Generates review cards:
      - Completion summary
      - Rejection cards (>=3 rejections)
      - In-progress cards
      - Blocked cards (>7 days)
      - Recurring task cards
   └─ Returns list of ReviewCard objects
   
3. Frontend
   └─ Displays cards sequentially
   └─ User responds to each card
   └─ Each response calls POST /api/reviews/cards/{id}/respond
   
4. Backend
   └─ Processes response:
      - State transitions (Complete → Completed, Parked, etc.)
      - Creates new tasks (for breakdown requests)
      - Captures reflective notes
      - Auto-creates next recurrence instance
   └─ Clears rejection dampening
   └─ Ready for next day
```

## Key Implementation Details

### Scoring Algorithm (Pseudocode)

```python
def calculate_task_score(task):
    base_score = (
        (importance_weight[task.importance] * IMPORTANCE_MULTIPLIER) +
        (urgency_weight[task.urgency] * URGENCY_MULTIPLIER)
    )
    
    # Strategic nudge for important-but-not-urgent tasks
    if task.importance == 'A' and task.urgency >= 3:
        base_score += STRATEGIC_NUDGE_BOOST
    
    # Apply rejection dampening
    if task.id in rejection_dampening:
        base_score = base_score / (1 + DAMPENING_FACTOR)
    
    # Apply daily priority boost
    if task.id in daily_priorities:
        base_score = base_score * PRIORITY_MULTIPLIER
    
    return base_score

def suggest_next_task():
    candidate_tasks = [t for t in ready_tasks if t.state == 'Ready']
    scores = [calculate_task_score(t) for t in candidate_tasks]
    probabilities = softmax(scores)  # Normalize to probabilities
    
    # Randomly select (not deterministic max)
    selected_task = random_select_by_probability(candidate_tasks, probabilities)
    return selected_task
```

### Dampening Session Lifecycle

```
┌──────────────────────────────────────────────────────┐
│ "What Next?" Suggestion Flow                         │
├──────────────────────────────────────────────────────┤
│                                                      │
│ User asks "what next?"                              │
│ → Suggest Task A                                    │
│                                                      │
│ User: "Not now, suggest another"                    │
│ → Apply dampening to Task A                         │
│ → Suggest Task B                                    │
│                                                      │
│ User: "Not now, suggest another"                    │
│ → Apply dampening to Task B                         │
│ → Suggest Task C                                    │
│                                                      │
│ User: "I'll take a break"                           │
│ → CLEAR ALL DAMPENING                              │
│ → End flow                                          │
│                                                      │
│ Later, user asks "what next?" again                 │
│ → Full candidate pool visible (no dampening)        │
│                                                      │
│ OR Evening Review occurs                            │
│ → CLEAR ALL DAMPENING (implicit)                    │
│ → New day, fresh slate                              │
└──────────────────────────────────────────────────────┘
```

## Testing Strategy

### Backend
- Unit tests for scoring algorithm (various task combinations)
- Integration tests for CRUD operations
- Tests for review card generation logic
- Tests for state transition rules

### Frontend
- Component tests for major pages (Morning Planning, Reviews)
- Store tests (Zustand state updates)
- Integration tests with mock API responses

### E2E
- Cypress or Playwright tests for core user flows (optional, v2)

## Security Considerations (MVP)

- Simple bearer token or session-based auth (no OAuth yet)
- No user account signup (single-user MVP)
- Environment variables for sensitive config (.env file)
- CORS configured for dev hosts only

## Deployment (Future)

- Backend: Docker container → Cloud Run, Heroku, or DigitalOcean
- Web: Static build → Vercel, Netlify, or GitHub Pages
- Mobile: Expo EAS Build for CI/CD, TestFlight/Play Store distribution

## Known Limitations & Deferred Features

- **No multi-user support** (v2)
- **No offline sync** (local-first currently, sync in v2)
- **No AI breakdown conversations** (review cards create a task for later, v2)
- **No mobile notifications** (nice-to-have)
- **No analytics dashboard** (avoid gamification)
- **No custom recurrence patterns** (daily/weekly only for MVP)

---

See [DEVELOPMENT.md](DEVELOPMENT.md) for setup and running locally.
