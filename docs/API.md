# API Documentation

API base URL: `http://localhost:8000/api`

Interactive API docs available at: `http://localhost:8000/docs` (Swagger UI)

## Authentication

This API uses **JWT-based authentication** with the HTTP Bearer scheme. All endpoints require a valid JWT access token provided in the `Authorization` header.

**Request Header:**
```
Authorization: Bearer <your-jwt-access-token>
```

**Authentication Requirements:**
- All Values endpoints require authentication
- Requests without a valid token will receive `401 Unauthorized`
- Data is scoped by `user_id` - users can only access their own values

**Security Notes:**
- Protect your JWT secret key (configured via `JWT_SECRET_KEY` environment variable)
- Use HTTPS in production to protect tokens in transit
- Tokens should be kept secure and not shared

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
- `statement` must not exceed 255 characters
- Leading/trailing whitespace is automatically trimmed

**Error Responses:**
- `400 Bad Request` - Empty or whitespace-only statement
- `400 Bad Request` - Statement exceeds maximum length of 255 characters
- `401 Unauthorized` - Missing or invalid JWT token

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

**Error Responses:**
- `401 Unauthorized` - Missing or invalid JWT token

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
- `statement` must not exceed 255 characters
- Leading/trailing whitespace is automatically trimmed

**Error Responses:**
- `400 Bad Request` - Empty or whitespace-only statement
- `400 Bad Request` - Statement exceeds maximum length of 255 characters
- `401 Unauthorized` - Missing or invalid JWT token
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
- `401 Unauthorized` - Missing or invalid JWT token
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
- `401 Unauthorized` - Authentication failed (missing or invalid JWT token)
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

## Security & Configuration

This API uses **JWT-based authentication** via the `HTTPBearer` scheme. All `/values` endpoints require a valid JWT access token and restrict data access by the authenticated user's `user_id`. Requests without a valid token are rejected with **401 Unauthorized**.

### Security Requirements

- **Protect your JWT secret**: Configure `JWT_SECRET_KEY` securely via environment variables or a secrets manager. Do **not** hard-code secrets in source code or commit them to version control.
- **Run the server in a trusted environment** and restrict who can obtain valid JWTs (for example, by controlling your user management and token-issuing process).
- If you expose the `/api` endpoints beyond localhost, ensure that transport is protected via HTTPS/SSL termination at a reverse proxy and that only trusted clients have access to valid JWTs.

### Current Configuration

By default, the server binds to `0.0.0.0`, which makes it reachable from other hosts on the network. However, the `/values` endpoints enforce JWT-based HTTP Bearer authentication and filter data by `user_id`, so only requests with a valid JWT can create, read, or modify a user's value records.

### Future Enhancements

Future versions may extend and harden authentication and authorization (for example, role-based access control, token refresh flows, or additional security options) for production deployments.
