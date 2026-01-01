# API Documentation

API base URL: `http://localhost:8000/api`

Interactive API docs available at: `http://localhost:8000/docs` (Swagger UI)

## Values Endpoints

User-defined values represent personal principles or goals (e.g., "I am improving in my craft", "My family comes first"). Values are linked to tasks to provide context and meaning.

### Create Value

**POST** `/values`

Create a new value statement.

**Request Body:**
```json
{
  "statement": "I am improving in my craft"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "statement": "I am improving in my craft",
  "archived": false,
  "created_at": "2026-01-01T12:00:00Z"
}
```

**Validation:**
- `statement` must not be empty or whitespace-only
- Leading/trailing whitespace is automatically trimmed

**Error Responses:**
- `400 Bad Request` - Empty or whitespace-only statement

---

### List Active Values

**GET** `/values`

List all active (non-archived) values.

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "statement": "I am improving in my craft",
    "archived": false,
    "created_at": "2026-01-01T12:00:00Z"
  },
  {
    "id": 2,
    "statement": "My family comes first",
    "archived": false,
    "created_at": "2026-01-01T12:05:00Z"
  }
]
```

**Notes:**
- Archived values are excluded from this list
- Returns empty array `[]` if no active values exist

---

### Update Value

**PUT** `/values/{value_id}`

Update a value's statement.

**Path Parameters:**
- `value_id` (integer) - The ID of the value to update

**Request Body:**
```json
{
  "statement": "I am mastering my craft"
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "statement": "I am mastering my craft",
  "archived": false,
  "created_at": "2026-01-01T12:00:00Z"
}
```

**Validation:**
- `statement` must not be empty or whitespace-only
- Leading/trailing whitespace is automatically trimmed

**Error Responses:**
- `400 Bad Request` - Empty or whitespace-only statement
- `404 Not Found` - Value with given ID does not exist

---

### Archive Value

**PATCH** `/values/{value_id}/archive`

Archive (deactivate) a value. Archived values are excluded from the active values list but do not affect existing task-value links.

**Path Parameters:**
- `value_id` (integer) - The ID of the value to archive

**Response:** `200 OK`
```json
{
  "id": 1,
  "statement": "I am improving in my craft",
  "archived": true,
  "created_at": "2026-01-01T12:00:00Z"
}
```

**Notes:**
- Archived values do not affect existing task-value associations
- Tasks linked to archived values retain their links
- Archived values can still be updated via PUT endpoint
- Archived values are excluded from GET /values listing

**Error Responses:**
- `404 Not Found` - Value with given ID does not exist

---

## Tasks Endpoints

*Coming soon*

---

## Suggestions Endpoints

*Coming soon*

---

## Reviews Endpoints

*Coming soon*

---

## Error Response Format

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- `200 OK` - Request succeeded
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data or validation error
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## Data Models

### Value

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | integer | - | Auto-generated unique identifier |
| `statement` | string | Yes | The value statement (max 255 chars) |
| `archived` | boolean | - | Whether the value is archived (default: false) |
| `created_at` | datetime | - | Timestamp when value was created |

---

## Authentication & Security

**⚠️ IMPORTANT SECURITY NOTICE**

This API currently has **no authentication or authorization** and is intended for a **single-user, local-only deployment**.

### Security Requirements

- **Run the server only in a trusted environment** (for example, bound to `127.0.0.1` or on a host/firewall that blocks external access).
- **Do NOT expose the `/api` endpoints directly to the public internet or any untrusted network.**
- If you need remote or multi-user access, you **must** first add an authentication/authorization layer (for example, bearer tokens or session-based auth) or place this service behind an authenticated reverse proxy/gateway.

### Current Configuration

The default server configuration binds to `0.0.0.0`, which means any network client that can reach the service can create, read, and modify value records and other data, which may include sensitive personal information.

### Future Enhancements

Future versions will include bearer token or session-based authentication for production deployments.
