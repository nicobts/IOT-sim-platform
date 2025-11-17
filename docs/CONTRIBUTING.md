# Contributing to FastAPI 1NCE Server

Thank you for your interest in contributing to the FastAPI 1NCE Server project! This document provides guidelines and instructions for contributing.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)

## 🤝 Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

**Positive behavior includes:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Unacceptable behavior includes:**
- Trolling, insulting/derogatory comments, and personal attacks
- Public or private harassment
- Publishing others' private information without permission
- Other conduct which could reasonably be considered inappropriate

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Git
- 1NCE API credentials (for integration testing)

### Setting Up Development Environment

1. **Fork the repository**
```bash
git clone https://github.com/yourusername/fastapi-1nce-server.git
cd fastapi-1nce-server
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements-dev.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Start development services**
```bash
docker-compose up -d db redis
```

6. **Run database migrations**
```bash
alembic upgrade head
```

7. **Install pre-commit hooks**
```bash
pre-commit install
```

## 💻 Development Workflow

### Branch Strategy

- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Critical production fixes
- `release/*` - Release preparation

### Creating a Feature

1. **Create a feature branch**
```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

2. **Make your changes**
```bash
# Write code, tests, and documentation
```

3. **Run tests and linters**
```bash
# Format code
black app tests
isort app tests

# Lint
ruff check app tests

# Type check
mypy app

# Run tests
pytest

# Check coverage
pytest --cov=app --cov-report=html
```

4. **Commit your changes**
```bash
git add .
git commit -m "feat: add new feature"
```

5. **Push and create PR**
```bash
git push origin feature/your-feature-name
# Create PR on GitHub
```

## 📝 Coding Standards

### Python Style Guide

We follow [PEP 8](https://peps.python.org/pep-0008/) with some modifications:

- Line length: 100 characters (black default)
- Use type hints for all function signatures
- Use f-strings for string formatting
- Use async/await for asynchronous code

### Code Formatting

**Black** - Code formatter
```bash
black app tests
```

**isort** - Import sorting
```bash
isort app tests
```

**Ruff** - Fast linter
```bash
ruff check app tests
```

### Type Hints

Always use type hints:

```python
from typing import Optional, List
from app.schemas.sim import SIMInDB

async def get_sim(iccid: str) -> Optional[SIMInDB]:
    """Get SIM by ICCID."""
    pass

async def list_sims(
    skip: int = 0,
    limit: int = 100
) -> List[SIMInDB]:
    """List all SIMs with pagination."""
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def calculate_usage(
    volume_rx: int,
    volume_tx: int
) -> int:
    """
    Calculate total data usage.
    
    Args:
        volume_rx: Bytes received
        volume_tx: Bytes transmitted
        
    Returns:
        Total bytes used
        
    Raises:
        ValueError: If volume is negative
        
    Examples:
        >>> calculate_usage(1000, 500)
        1500
    """
    if volume_rx < 0 or volume_tx < 0:
        raise ValueError("Volume cannot be negative")
    return volume_rx + volume_tx
```

### Error Handling

Always use proper error handling:

```python
from app.core.exceptions import OnceAPIError
from fastapi import HTTPException
import structlog

logger = structlog.get_logger()

async def get_sim_data(iccid: str):
    try:
        sim = await once_client.get_sim(iccid)
        return sim
    except OnceAPIError as e:
        logger.error(
            "Failed to fetch SIM",
            iccid=iccid,
            error=str(e)
        )
        raise HTTPException(
            status_code=502,
            detail="Upstream API error"
        )
    except Exception as e:
        logger.exception("Unexpected error", iccid=iccid)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
```

## 🧪 Testing Guidelines

### Test Structure

```
tests/
├── unit/           # Fast, isolated tests
├── integration/    # Tests with database, Redis
└── e2e/           # End-to-end workflow tests
```

### Writing Tests

**Unit Test Example:**
```python
import pytest
from app.services.sim_service import SIMService

@pytest.mark.asyncio
async def test_calculate_total_usage():
    """Test usage calculation."""
    service = SIMService()
    total = service.calculate_total_usage(
        volume_rx=1000,
        volume_tx=500
    )
    assert total == 1500

@pytest.mark.asyncio
async def test_get_sim_not_found(mock_db):
    """Test SIM not found scenario."""
    service = SIMService(mock_db)
    result = await service.get_sim_by_iccid("invalid")
    assert result is None
```

**Integration Test Example:**
```python
import pytest
from app.db.session import get_session
from app.models.sim import SIM

@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_sim(db_session):
    """Test SIM creation in database."""
    sim = SIM(
        iccid="1234567890123456789",
        status="enabled"
    )
    db_session.add(sim)
    await db_session.commit()
    
    result = await db_session.get(SIM, sim.id)
    assert result.iccid == "1234567890123456789"
```

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/unit/test_sim_service.py

# Specific test
pytest tests/unit/test_sim_service.py::test_calculate_total_usage

# With coverage
pytest --cov=app --cov-report=html

# Only unit tests
pytest tests/unit/

# Only integration tests
pytest tests/integration/

# Skip slow tests
pytest -m "not slow"
```

### Test Coverage

- Minimum coverage: **80%**
- All new features must include tests
- Bug fixes should include regression tests
- Critical paths should have **90%+** coverage

## 📧 Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements
- `ci`: CI/CD changes

### Examples

```bash
# Feature
git commit -m "feat(sims): add bulk import functionality"

# Bug fix
git commit -m "fix(auth): resolve token refresh race condition"

# Documentation
git commit -m "docs(api): update SIM management endpoints"

# Breaking change
git commit -m "feat(api)!: change pagination to cursor-based

BREAKING CHANGE: Pagination now uses cursor instead of offset"
```

## 🔄 Pull Request Process

### Before Submitting

1. ✅ Code follows style guidelines
2. ✅ All tests pass
3. ✅ New code has tests
4. ✅ Documentation updated
5. ✅ Commit messages follow conventions
6. ✅ No merge conflicts with `develop`

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Related Issues
Closes #123

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
- [ ] Coverage maintained/improved
```

### Review Process

1. **Automated checks** must pass (CI/CD)
2. **Two approvals** required from maintainers
3. **All comments** must be addressed
4. **Squash and merge** to keep history clean

### After Merge

- Delete feature branch
- Update related issues
- Monitor CI/CD pipeline

## 🐛 Reporting Bugs

### Before Reporting

1. Check existing issues
2. Update to latest version
3. Verify it's reproducible

### Bug Report Template

```markdown
**Describe the bug**
Clear description of the bug

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What you expected to happen

**Actual behavior**
What actually happened

**Environment**
- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.11.5]
- FastAPI version: [e.g., 0.104.1]
- Docker version: [e.g., 24.0.5]

**Logs**
```
Paste relevant logs here
```

**Additional context**
Any other information
```

## 💡 Suggesting Features

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
Clear description of the problem

**Describe the solution you'd like**
What you want to happen

**Describe alternatives you've considered**
Other solutions you've thought about

**Use case**
How will this feature be used?

**Additional context**
Screenshots, mockups, etc.
```

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [1NCE API Documentation](https://help.1nce.com/dev-hub)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org)
- [pytest Documentation](https://docs.pytest.org)

## 🙋 Questions?

- Open a discussion on GitHub
- Join our Slack channel
- Email: dev@example.com

---

Thank you for contributing to FastAPI 1NCE Server! 🎉
