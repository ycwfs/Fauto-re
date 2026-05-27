# Full-Auto-Research

A complete, production-ready, multi-user AI research automation platform that integrates paper discovery, autonomous experiments, and academic paper writing into a unified workflow.

## Features

### Three-Stage Research Workflow

1. **Paper Discovery → Ideas**
   - Automated arXiv paper fetching based on keywords and categories
   - Full-text bilingual summarization (Chinese/English)
   - Trend analysis with TF-IDF, LDA, and word clouds
   - Zotero integration for research management
   - Weekly research idea generation

2. **Ideas → Experiments**
   - Autonomous experiment framework with self-improvement loops
   - Fixed time-budget evaluation
   - Modify → Test → Evaluate → Keep/Discard iterations
   - Git-based experiment branching
   - Real-time progress monitoring

3. **Experiments → Paper**
   - Section-by-section academic paper generation
   - LaTeX and Markdown support
   - Venue-specific templates (NeurIPS, ICML, ACL, etc.)
   - Figure generation integration
   - Citation management

### Multi-User Platform

- User authentication and authorization (JWT)
- Per-user data isolation
- Subscription tiers (Free, Pro, Enterprise)
- Stripe payment integration
- Usage limits and quota enforcement
- RESTful API for programmatic access

## Technology Stack

**Backend:**
- FastAPI (Python 3.12)
- PostgreSQL 16
- Redis 7
- Celery (background jobs)
- SQLAlchemy 2.0 + Alembic
- Stripe (payments)

**Frontend:**
- React 18 + TypeScript
- Vite + Tailwind CSS
- TanStack Query
- Zustand (state management)
- Recharts (visualization)

**Deployment:**
- Docker + Docker Compose
- Kubernetes (DigitalOcean)
- GitHub Actions (CI/CD)
- Nginx (reverse proxy)

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 16
- Redis 7
- Docker & Docker Compose (for deployment)

### Local Development

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/Full-Auto-Reasearch.git
cd Full-Auto-Reasearch
```

2. **Set up backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

3. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Run database migrations:**
```bash
alembic upgrade head
```

5. **Start backend services:**
```bash
# Terminal 1: API server
uvicorn src.main:app --reload

# Terminal 2: Celery worker
celery -A src.services.tasks worker --loglevel=info
```

6. **Set up frontend:**
```bash
cd frontend
npm install
npm run dev
```

7. **Access the application:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Docker Compose (Recommended)

```bash
docker-compose up -d
```

This starts all services: PostgreSQL, Redis, backend, Celery worker, and frontend.

## Configuration

### Backend Configuration

Edit `backend/.env`:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/full_auto_research

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-password
```

### Frontend Configuration

Edit `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
```

## API Documentation

Interactive API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Key Endpoints

**Authentication:**
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token

**Papers:**
- `GET /api/papers/` - List papers (paginated)
- `POST /api/papers/fetch` - Trigger paper fetching
- `GET /api/papers/stats` - Get statistics

**Experiments:**
- `POST /api/experiments/` - Create experiment
- `POST /api/experiments/{id}/start` - Start experiment
- `GET /api/experiments/{id}/status` - Get status

**Paper Writing:**
- `POST /api/writing/papers` - Create paper draft
- `POST /api/writing/papers/{id}/outline` - Generate outline
- `POST /api/writing/papers/{id}/sections/{section}` - Generate section

**Subscriptions:**
- `GET /api/subscriptions/current` - Get current subscription
- `POST /api/subscriptions/checkout` - Create checkout session
- `POST /api/subscriptions/cancel` - Cancel subscription

## Subscription Tiers

| Feature | Free | Pro | Enterprise |
|---------|------|-----|------------|
| Papers per day | 10 | 100 | Unlimited |
| Experiments per week | 1 | Unlimited | Unlimited |
| Storage | 1 GB | 10 GB | Custom |
| Support | Community | Priority | Dedicated |
| API Access | ❌ | ✅ | ✅ |
| Price | $0 | $29/mo | $99/mo |

## Project Structure

```
Full-Auto-Reasearch/
├── backend/              # FastAPI backend
│   ├── src/
│   │   ├── api/         # API endpoints
│   │   ├── models/      # Database models
│   │   ├── services/    # Business logic
│   │   └── utils/       # Utilities
│   ├── tests/           # Test suite
│   └── alembic/         # Database migrations
├── frontend/            # React frontend
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── pages/       # Page components
│   │   ├── api/         # API client
│   │   └── store/       # State management
│   └── public/          # Static assets
├── infrastructure/      # Deployment configs
│   ├── k8s/            # Kubernetes manifests
│   └── terraform/      # Infrastructure as code
├── .github/
│   └── workflows/      # CI/CD pipelines
└── docker-compose.yml  # Local development
```

## Testing

### Backend Tests

```bash
cd backend
pytest --cov=src tests/
```

Test coverage includes:
- Authentication and authorization
- API endpoints
- Database models
- Background tasks
- Security vulnerabilities
- End-to-end workflows

### Frontend Tests

```bash
cd frontend
npm run test
npm run test:e2e
```

## Deployment

### Kubernetes (Production)

1. **Set up DigitalOcean Kubernetes cluster:**
```bash
doctl kubernetes cluster create full-auto-research \
  --region nyc1 \
  --node-pool "name=worker-pool;size=s-2vcpu-4gb;count=3"
```

2. **Configure kubectl:**
```bash
doctl kubernetes cluster kubeconfig save full-auto-research
```

3. **Create secrets:**
```bash
kubectl create secret generic app-secrets \
  --from-literal=database-url=$DATABASE_URL \
  --from-literal=redis-url=$REDIS_URL \
  --from-literal=secret-key=$SECRET_KEY \
  --from-literal=stripe-secret-key=$STRIPE_SECRET_KEY \
  -n production
```

4. **Deploy:**
```bash
kubectl apply -f infrastructure/k8s/
```

5. **Verify deployment:**
```bash
kubectl get pods -n production
kubectl get ingress -n production
```

### CI/CD

GitHub Actions automatically:
- Runs tests on pull requests
- Builds Docker images on merge to main
- Deploys to Kubernetes cluster
- Runs database migrations

Configure secrets in GitHub repository settings:
- `DIGITALOCEAN_ACCESS_TOKEN`
- `CLUSTER_NAME`

## Security

- HTTPS/TLS 1.3 encryption
- JWT authentication with bcrypt password hashing
- SQL injection protection (parameterized queries)
- XSS prevention (input sanitization)
- CSRF protection
- Rate limiting
- API key rotation
- Secrets management

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Support

- Documentation: https://docs.full-auto-research.com
- Issues: https://github.com/yourusername/Full-Auto-Reasearch/issues
- Email: support@full-auto-research.com

## Acknowledgments

- Auto-Research: Original paper discovery system
- autoresearch: Autonomous experiment framework
- Zotero: Research management integration
- MinerU: PDF extraction
- Claude/GPT: AI assistance
