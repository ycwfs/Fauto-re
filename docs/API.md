# API Documentation

Full-Auto-Research REST API reference.

## Base URL

- Development: `http://localhost:8000`
- Production: `https://api.full-auto-research.com`

## Authentication

All authenticated endpoints require a JWT token in the Authorization header:

```
Authorization: Bearer <token>
```

Get a token by logging in via `/api/auth/login`.

## Endpoints

### Authentication

#### Register User

```http
POST /api/auth/register
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "John Doe"
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### Login

```http
POST /api/auth/login
```

**Request Body (form-data):**
```
username: user@example.com
password: securepassword123
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Users

#### Get Current User

```http
GET /api/users/me
```

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### Get User Preferences

```http
GET /api/users/preferences
```

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "id": 1,
  "user_id": 1,
  "arxiv_categories": ["cs.AI", "cs.LG"],
  "keywords": ["machine learning", "deep learning"],
  "max_papers_per_day": 50,
  "summary_language": "en",
  "notification_email": true,
  "weekly_digest_day": "thursday"
}
```

#### Update User Preferences

```http
PUT /api/users/preferences
```

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "arxiv_categories": ["cs.AI", "cs.CL"],
  "keywords": ["NLP", "transformers"],
  "max_papers_per_day": 100
}
```

**Response:** `200 OK` (updated preferences)

### Papers

#### List Papers

```http
GET /api/papers/?page=1&size=50
```

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `size` (optional): Items per page (default: 50, max: 100)

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": 1,
      "arxiv_id": "2024.12345",
      "title": "Novel Approach to AI",
      "authors": "John Doe, Jane Smith",
      "abstract": "This paper presents...",
      "categories": "cs.AI",
      "published_date": "2024-01-01T00:00:00Z",
      "pdf_url": "https://arxiv.org/pdf/2024.12345.pdf",
      "created_at": "2024-01-01T12:00:00Z"
    }
  ],
  "total": 150,
  "page": 1,
  "size": 50,
  "pages": 3
}
```

#### Get Paper

```http
GET /api/papers/{paper_id}
```

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK` (single paper object)

#### Get Paper Statistics

```http
GET /api/papers/stats
```

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "total_papers": 150,
  "papers_this_week": 25,
  "papers_this_month": 100,
  "categories": {
    "cs.AI": 80,
    "cs.LG": 70
  }
}
```

#### Trigger Paper Fetch

```http
POST /api/papers/fetch
```

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "status": "started",
  "task_id": "abc123-def456-ghi789"
}
```

### Ideas

#### List Ideas

```http
GET /api/ideas/
```

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "user_id": 1,
    "title": "Improve Model Efficiency",
    "description": "Based on recent papers...",
    "keywords": ["efficiency", "optimization"],
    "status": "pending",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

#### Create Idea

```http
POST /api/ideas/
```

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "title": "New Research Direction",
  "description": "Exploring novel approaches...",
  "keywords": ["novel", "approach"]
}
```

**Response:** `200 OK` (created idea)

#### Approve Idea

```http
POST /api/ideas/{idea_id}/approve
```

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "id": 1,
  "status": "approved",
  "approved_at": "2024-01-01T12:00:00Z"
}
```

### Experiments

#### List Experiments

```http
GET /api/experiments/
```

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "user_id": 1,
    "name": "Efficiency Experiment",
    "description": "Testing improvements...",
    "base_repo_url": "https://github.com/user/repo",
    "status": "running",
    "created_at": "2024-01-01T00:00:00Z",
    "started_at": "2024-01-01T01:00:00Z"
  }
]
```

#### Create Experiment

```http
POST /api/experiments/
```

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "name": "New Experiment",
  "description": "Testing hypothesis...",
  "base_repo_url": "https://github.com/user/repo",
  "goals": "Improve accuracy by 10%",
  "idea_id": 1
}
```

**Response:** `200 OK` (created experiment)

#### Get Experiment

```http
GET /api/experiments/{experiment_id}
```

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK` (single experiment object)

#### Start Experiment

```http
POST /api/experiments/{experiment_id}/start
```

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "id": 1,
  "status": "setting_up",
  "task_id": "setup-task-123"
}
```

#### Stop Experiment

```http
POST /api/experiments/{experiment_id}/stop
```

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "id": 1,
  "status": "stopping"
}
```

#### Get Experiment Status

```http
GET /api/experiments/{experiment_id}/status
```

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "id": 1,
  "status": "running",
  "progress": 45,
  "current_iteration": 9,
  "total_iterations": 20,
  "results": {
    "best_score": 0.85,
    "improvements": 3
  }
}
```

### Paper Writing

#### List Papers

```http
GET /api/writing/papers
```

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "user_id": 1,
    "experiment_id": 1,
    "title": "Efficient AI Models",
    "venue": "NeurIPS",
    "status": "draft",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

#### Create Paper

```http
POST /api/writing/papers
```

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "experiment_id": 1,
  "venue": "NeurIPS",
  "title": "Novel Approach to AI"
}
```

**Response:** `200 OK` (created paper)

#### Generate Outline

```http
POST /api/writing/papers/{paper_id}/outline
```

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "id": 1,
  "outline": {
    "title": "Efficient AI Models",
    "sections": [
      "Introduction",
      "Related Work",
      "Method",
      "Experiments",
      "Conclusion"
    ]
  }
}
```

#### Generate Section

```http
POST /api/writing/papers/{paper_id}/sections/{section_name}
```

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "id": 1,
  "section": "introduction",
  "content": "# Introduction\n\nThis paper presents..."
}
```

#### Convert to LaTeX

```http
POST /api/writing/papers/{paper_id}/latex
```

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "id": 1,
  "latex_content": "\\documentclass{article}..."
}
```

#### Download Paper

```http
GET /api/writing/papers/{paper_id}/download?format=markdown
```

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `format`: `markdown` or `latex`

**Response:** `200 OK` (file download)

### Subscriptions

#### Get Current Subscription

```http
GET /api/subscriptions/current
```

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "id": 1,
  "user_id": 1,
  "plan": "pro",
  "status": "active",
  "stripe_subscription_id": "sub_123",
  "current_period_start": "2024-01-01T00:00:00Z",
  "current_period_end": "2024-02-01T00:00:00Z"
}
```

#### Create Checkout Session

```http
POST /api/subscriptions/checkout
```

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "plan": "pro"
}
```

**Response:** `200 OK`
```json
{
  "checkout_url": "https://checkout.stripe.com/session_123"
}
```

#### Cancel Subscription

```http
POST /api/subscriptions/cancel
```

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "status": "success",
  "message": "Subscription will be canceled at period end"
}
```

#### Get Usage Limits

```http
GET /api/subscriptions/limits
```

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "plan": "pro",
  "papers_per_day": 100,
  "experiments_per_week": -1,
  "storage_gb": 10,
  "api_access": true
}
```

## Error Responses

### 400 Bad Request

```json
{
  "detail": "Invalid request parameters"
}
```

### 401 Unauthorized

```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden

```json
{
  "detail": "Not enough permissions"
}
```

### 404 Not Found

```json
{
  "detail": "Resource not found"
}
```

### 422 Validation Error

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 429 Too Many Requests

```json
{
  "detail": "Rate limit exceeded"
}
```

### 500 Internal Server Error

```json
{
  "detail": "Internal server error"
}
```

## Rate Limits

- Free tier: 100 requests/hour
- Pro tier: 1000 requests/hour
- Enterprise tier: 10000 requests/hour

## Webhooks

### Stripe Webhook

```http
POST /api/subscriptions/webhook
```

**Headers:**
- `stripe-signature`: Stripe signature for verification

**Events Handled:**
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.payment_succeeded`
- `invoice.payment_failed`

## SDKs

### Python

```python
import requests

class FullAutoResearchClient:
    def __init__(self, api_url, token):
        self.api_url = api_url
        self.headers = {"Authorization": f"Bearer {token}"}
    
    def list_papers(self, page=1, size=50):
        response = requests.get(
            f"{self.api_url}/api/papers/",
            params={"page": page, "size": size},
            headers=self.headers
        )
        return response.json()
    
    def create_experiment(self, name, description, base_repo_url, goals):
        response = requests.post(
            f"{self.api_url}/api/experiments/",
            json={
                "name": name,
                "description": description,
                "base_repo_url": base_repo_url,
                "goals": goals
            },
            headers=self.headers
        )
        return response.json()

# Usage
client = FullAutoResearchClient("https://api.full-auto-research.com", "your-token")
papers = client.list_papers()
```

### JavaScript

```javascript
class FullAutoResearchClient {
  constructor(apiUrl, token) {
    this.apiUrl = apiUrl;
    this.headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  async listPapers(page = 1, size = 50) {
    const response = await fetch(
      `${this.apiUrl}/api/papers/?page=${page}&size=${size}`,
      { headers: this.headers }
    );
    return response.json();
  }

  async createExperiment(name, description, baseRepoUrl, goals) {
    const response = await fetch(
      `${this.apiUrl}/api/experiments/`,
      {
        method: 'POST',
        headers: this.headers,
        body: JSON.stringify({
          name,
          description,
          base_repo_url: baseRepoUrl,
          goals
        })
      }
    );
    return response.json();
  }
}

// Usage
const client = new FullAutoResearchClient('https://api.full-auto-research.com', 'your-token');
const papers = await client.listPapers();
```
