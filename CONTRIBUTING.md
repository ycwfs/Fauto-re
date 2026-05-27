# Contributing to Full-Auto-Research

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Respect differing viewpoints and experiences

## Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/Full-Auto-Reasearch.git
cd Full-Auto-Reasearch
```

### 2. Set Up Development Environment

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Frontend
cd ../frontend
npm install
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

## Development Workflow

### Backend Development

1. **Make your changes** in `backend/src/`

2. **Write tests** in `backend/tests/`
   ```bash
   pytest tests/test_your_feature.py
   ```

3. **Run linting**
   ```bash
   ruff check src/
   black --check src/
   mypy src/
   ```

4. **Format code**
   ```bash
   black src/
   ruff check --fix src/
   ```

5. **Run all tests**
   ```bash
   pytest --cov=src tests/
   ```

### Frontend Development

1. **Make your changes** in `frontend/src/`

2. **Run linting**
   ```bash
   npm run lint
   ```

3. **Run tests**
   ```bash
   npm test
   ```

4. **Build to verify**
   ```bash
   npm run build
   ```

### Database Migrations

If you modify database models:

```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
```

## Coding Standards

### Python (Backend)

- Follow PEP 8 style guide
- Use type hints for all functions
- Maximum line length: 100 characters
- Use docstrings for all public functions/classes
- Use `black` for formatting
- Use `ruff` for linting

Example:
```python
from typing import List, Optional
from sqlalchemy.orm import Session

def get_papers(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 50
) -> List[Paper]:
    """
    Retrieve papers for a user with pagination.

    Args:
        db: Database session
        user_id: ID of the user
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of Paper objects
    """
    return db.query(Paper)\
        .filter(Paper.user_id == user_id)\
        .offset(skip)\
        .limit(limit)\
        .all()
```

### TypeScript (Frontend)

- Use TypeScript strict mode
- Use functional components with hooks
- Use meaningful variable names
- Maximum line length: 100 characters
- Use ESLint for linting
- Use Prettier for formatting

Example:
```typescript
interface PaperListProps {
  userId: number;
  onPaperClick: (paperId: number) => void;
}

export const PaperList: React.FC<PaperListProps> = ({ userId, onPaperClick }) => {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPapers(userId).then(setPapers).finally(() => setLoading(false));
  }, [userId]);

  if (loading) return <Spinner />;

  return (
    <div className="paper-list">
      {papers.map(paper => (
        <PaperCard
          key={paper.id}
          paper={paper}
          onClick={() => onPaperClick(paper.id)}
        />
      ))}
    </div>
  );
};
```

## Testing Guidelines

### Backend Tests

- Write tests for all new features
- Aim for >80% code coverage
- Use pytest fixtures for common setup
- Mock external services (Stripe, email, etc.)
- Test both success and error cases

Test structure:
```python
def test_feature_success(client, auth_headers):
    """Test successful feature execution."""
    response = client.post("/api/endpoint", headers=auth_headers, json={...})
    assert response.status_code == 200
    assert response.json()["key"] == "expected_value"

def test_feature_validation_error(client, auth_headers):
    """Test validation error handling."""
    response = client.post("/api/endpoint", headers=auth_headers, json={})
    assert response.status_code == 422

def test_feature_unauthorized(client):
    """Test unauthorized access."""
    response = client.post("/api/endpoint", json={...})
    assert response.status_code == 401
```

### Frontend Tests

- Write tests for all components
- Test user interactions
- Test error states
- Use React Testing Library

## Commit Messages

Follow conventional commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(api): add paper search endpoint

Implement full-text search for papers using PostgreSQL's
full-text search capabilities.

Closes #123
```

```
fix(auth): prevent token expiration race condition

Add token refresh mechanism to prevent users from being
logged out during active sessions.

Fixes #456
```

## Pull Request Process

### 1. Update Your Branch

```bash
git fetch upstream
git rebase upstream/main
```

### 2. Run Tests

```bash
# Backend
cd backend
pytest --cov=src tests/

# Frontend
cd frontend
npm test
npm run build
```

### 3. Push Your Changes

```bash
git push origin feature/your-feature-name
```

### 4. Create Pull Request

- Go to GitHub and create a pull request
- Fill out the PR template
- Link related issues
- Request review from maintainers

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests pass locally
```

## Review Process

1. **Automated checks** must pass:
   - Tests
   - Linting
   - Type checking
   - Build

2. **Code review** by maintainers:
   - Code quality
   - Test coverage
   - Documentation
   - Security considerations

3. **Approval** required from at least one maintainer

4. **Merge** by maintainer after approval

## Areas for Contribution

### High Priority

- Rate limiting implementation
- API key authentication
- Audit logging system
- GDPR compliance features
- Performance optimizations

### Medium Priority

- Additional paper sources (beyond arXiv)
- More venue templates for paper writing
- Enhanced visualization for trend analysis
- Mobile app development
- Browser extension

### Documentation

- User guides
- API examples
- Video tutorials
- Architecture diagrams
- Deployment guides

### Testing

- Increase test coverage
- Add E2E tests
- Performance benchmarks
- Security testing

## Questions?

- Open an issue for questions
- Join our Discord: [link]
- Email: dev@full-auto-research.com

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
