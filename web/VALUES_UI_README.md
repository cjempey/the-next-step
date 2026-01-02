# Values Management UI - Setup Guide

## Quick Start

### 1. Set up backend
```bash
# Terminal 1: Start the backend
cd backend
uv run uvicorn app.main:app --reload
```

### 2. Create a test user and get auth token

**Option A: Use the script (easiest)**
```bash
cd backend
uv run python scripts/create_test_user.py

# Or with custom credentials:
# uv run python scripts/create_test_user.py myuser test@example.com mypass123
```

The script will output a JWT token. Copy it for step 3.

**Option B: Manual with curl**
```bash
# Register a test user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"testpass123"}'

# Login to get JWT token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}'

# Copy the "access_token" value from the response
```

### 3. Configure web app
```bash
cd web

# Copy example env file
cp .env.example .env

# Edit .env and paste your JWT token
# VITE_AUTH_TOKEN=your_jwt_token_here
```

### 4. Start web app
```bash
# Terminal 2: Start the web dev server
cd web
npm run dev
```

Open http://localhost:5173 in your browser.

## Features Implemented

### ✅ Active Values Management
- Display list of all active (non-archived) values
- Create new values with validation:
  - Max 255 characters
  - No empty or whitespace-only statements
  - Automatic trimming of leading/trailing whitespace
- Inline editing of value statements
- Archive values with confirmation dialog

### ✅ Archived Values Section
- Separate section for archived values
- Display created date
- Show archive date placeholder (API doesn't track yet - see issue #16)
- Show task count (hardcoded to 0 - Task API not implemented yet)
- Unarchive functionality to restore values

### ✅ API Integration
- Full Values API client with TypeScript types
- Error handling with user-friendly messages
- Loading states during API calls
- JWT authentication via environment variable

### ✅ User Experience
- Responsive layout (mobile-friendly)
- Neutral, non-judgemental tone
- Clear validation messages
- Confirmation before destructive actions
- Character counter for input fields

## API Endpoints Used

- `GET /api/values?include_archived=true` - List all values
- `POST /api/values` - Create new value
- `PUT /api/values/{id}` - Update value statement
- `PATCH /api/values/{id}/archive` - Archive/unarchive value (toggles)

## Known Limitations (By Design)

1. **Archive date not tracked**: API doesn't have `archived_at` field yet (issue #16)
2. **Task counts hardcoded to 0**: Task API not implemented yet
3. **Hardcoded auth token**: Auth UI is future work, using env variable for now
4. **No frontend tests**: Manual verification acceptable for MVP

## Development

### Run linter
```bash
cd web
npm run lint
```

### Run type checker
```bash
cd web
npm run type-check
```

### Build for production
```bash
cd web
npm run build
```

## Troubleshooting

### "401 Unauthorized" errors
- Make sure backend is running
- Verify your JWT token is correct in `.env`
- Token may have expired - login again to get a new one

### Backend not responding
- Check backend is running on http://localhost:8000
- Test with: `curl http://localhost:8000/api/health` (if health endpoint exists)

### Can't create values
- Check browser console for errors
- Verify value statement is not empty and under 255 characters
- Check backend logs for any errors
