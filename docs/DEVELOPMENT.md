# Development Setup & Workflow

## Prerequisites

- Python 3.11+ (with `uv` package manager)
- Node.js 18+ with npm
- PostgreSQL 14+ (local or Docker)
- Git

## Backend Setup

### 1. Create Virtual Environment & Install Dependencies

```bash
cd backend
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
uv pip install -e ".[dev]"  # Install dev dependencies too
```

### 2. Database Setup

#### Option A: Local PostgreSQL

```bash
# Create database and user
createuser nextstepapiuser -P  # Prompts for password
createdb -O nextstepapiuser the_next_step
```

#### Option B: Docker (Recommended)

```bash
docker run -d \
  --name postgres-nextStep \
  -e POSTGRES_USER=nextstepapiuser \
  -e POSTGRES_PASSWORD=changeme \
  -e POSTGRES_DB=the_next_step \
  -p 5432:5432 \
  postgres:15
```

### 3. Create `.env` File

```bash
cp .env.example .env
# Edit .env with your database credentials
```

Example `.env`:
```
DATABASE_URL=postgresql://nextstepapiuser:changeme@localhost:5432/the_next_step
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
OPENAI_API_KEY=sk-...  # Optional
```

### 4. Run Database Migrations

```bash
alembic upgrade head
```

This creates all tables from the `app/models.py` ORM definitions.

### 5. Run the Backend

```bash
python run.py
# Or with uvicorn directly:
uvicorn app.main:app --reload --port 8000
```

Server runs at `http://localhost:8000`  
API docs at `http://localhost:8000/docs` (Swagger UI)

## Web Frontend Setup

### 1. Install Dependencies

```bash
cd web
npm install
```

### 2. Run Development Server

```bash
npm run dev
```

Server runs at `http://localhost:5173`

The Vite config includes a proxy to `http://localhost:8000/api`, so API calls work seamlessly.

### 3. Build for Production

```bash
npm run build
npm run preview  # Preview production build locally
```

## Mobile Frontend Setup

### 1. Install Dependencies

```bash
cd mobile
npm install
```

### 2. Run Development Server

```bash
npm start
```

Expo CLI opens; choose:
- `a` for Android (requires Android Studio/Emulator)
- `i` for iOS (requires Xcode/Simulator, macOS only)
- `w` for web (browser)

### 3. Install on Device

For physical device testing:
- Download Expo Go app (iOS App Store or Google Play)
- Scan QR code from CLI output

## Running Everything Together

### Convenient Local Setup Script

Create `run.sh` (macOS/Linux) or `run.bat` (Windows):

**run.sh:**
```bash
#!/bin/bash

# Start backend
echo "Starting backend..."
cd backend
source .venv/bin/activate
python run.py &
BACKEND_PID=$!

# Start web frontend
echo "Starting web frontend..."
cd ../web
npm run dev &
WEB_PID=$!

# Start mobile (optional)
echo "Starting mobile frontend..."
cd ../mobile
npm start &
MOBILE_PID=$!

echo "All services running. Press Ctrl+C to stop all."
wait
```

```bash
chmod +x run.sh
./run.sh
```

---

## GitHub Workflow (Recommended)

1. **Create a feature branch**
   ```bash
   git checkout -b feature/task-crud
   ```

2. **Make changes** (backend, web, mobile, or docs)

3. **Run tests locally**
   ```bash
   cd backend && pytest
   cd ../web && npm run type-check && npm run lint
   ```

4. **Commit with clear messages**
   ```bash
   git commit -m "feat(backend): implement task CRUD endpoints"
   ```

5. **Push and create a Pull Request**
   ```bash
   git push origin feature/task-crud
   ```

6. **GitHub Actions runs CI checks**
   - Linting
   - Type checking
   - Tests
   - Build verification

7. **Review, iterate, merge**

---

## Database Migrations with Alembic

### Create a New Migration

After modifying `app/models.py`, generate a migration:

```bash
alembic revision --autogenerate -m "Add task recurrence field"
```

This creates a file in `alembic/versions/` that you review and commit.

### Apply Migrations

```bash
alembic upgrade head  # Apply all pending migrations
alembic downgrade -1  # Rollback one migration
```

---

## Testing

### Backend Unit Tests

```bash
cd backend
pytest -v
```

Example test:

```python
# tests/test_scoring.py
def test_scoring_algorithm():
    task = Task(importance='A', urgency=3)
    score = calculate_task_score(task)
    assert score > 0
```

### Frontend Tests (Future)

```bash
cd web
npm test
```

---

## Debugging

### Backend Debugging

FastAPI + Uvicorn in reload mode makes development easy:

```bash
python run.py
# Changes to `app/` files reload automatically
```

For deeper debugging, use Python's debugger:

```python
import pdb; pdb.set_trace()
```

Or use VS Code's debugger with `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload"],
      "jinja": true,
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

### Web Debugging

React DevTools browser extension + Vite HMR make frontend development smooth.

---

## Linting & Formatting

### Backend

```bash
cd backend

# Format with Black
black app/ tests/

# Lint with Ruff
ruff check app/ tests/

# Type check with mypy
mypy app/
```

### Web

```bash
cd web

# ESLint
npm run lint

# Format with Prettier (if installed)
npx prettier --write src/
```

---

## Useful Commands Reference

| Command | Purpose |
|---------|---------|
| `uv pip install -r requirements.txt` | Install Python deps |
| `alembic upgrade head` | Run migrations |
| `alembic downgrade -1` | Rollback one migration |
| `python run.py` | Start backend |
| `npm run dev` | Start web frontend |
| `npm start` | Start mobile frontend |
| `pytest` | Run backend tests |
| `npm run type-check` | TypeScript type checking |
| `npm run lint` | Lint web code |
| `git checkout -b feature/...` | Create feature branch |
| `git push origin feature/...` | Push to GitHub |

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'app'"

Make sure you're running from the `backend/` directory:

```bash
cd backend
python run.py
```

### "Connection refused" to database

Check that PostgreSQL is running:

```bash
psql -U nextstepapiuser -d the_next_step
```

Or restart Docker container:

```bash
docker start postgres-nextStep
```

### API calls from frontend fail (CORS error)

Ensure backend is running at `http://localhost:8000` and the Vite config includes the proxy setting.

### Vite hot reload not working

Restart the dev server:

```bash
npm run dev
```

---

## Next Steps

1. Set up backend database migrations
2. Implement task CRUD endpoints
3. Implement scoring algorithm
4. Build web UI for morning planning
5. Build mobile UI for "what next?"
6. Connect frontends to backend
7. Implement evening review card system
8. Add tests and CI/CD

See [MVP_Requirements.md](../MVP_Requirements.md) for detailed feature specifications.
