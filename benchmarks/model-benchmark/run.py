#!/usr/bin/env python3
"""
Paridhi Model Benchmark: Kimi K2.7-Code vs MiMo-V2.5
Tests long-context agent tasks via OpenClaw gateway.
"""

import json
import time
import os
import sys
import subprocess
from datetime import datetime

# Benchmark tests
TESTS = [
    {
        "id": "long-context-memory",
        "name": "Long-Context Memory & Retrieval",
        "description": "Process a large synthetic codebase and answer specific questions about it",
        "weight": 20,
        "prompt": """You are given a large codebase context below. After processing, answer the following questions.

CODEBASE:
```python
# File: src/models/user.py (420 lines)
class User:
    def __init__(self, id, name, email, role, created_at, updated_at):
        self.id = id
        self.name = name
        self.email = email
        self.role = role
        self.created_at = created_at
        self.updated_at = updated_at
    
    def has_permission(self, permission):
        return permission in self.role.permissions
    
    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email, "role": self.role.name}
    
    def validate_email(self):
        import re
        return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', self.email))

# File: src/models/session.py (380 lines)
class Session:
    TOKEN_EXPIRY = 3600
    MAX_TOKENS = 1000
    def __init__(self, user_id, token, expires_at, ip_address, user_agent):
        self.user_id = user_id
        self.token = token
        self.expires_at = expires_at
        self.ip_address = ip_address
        self.user_agent = user_agent
    
    def is_expired(self):
        from datetime import datetime
        return datetime.utcnow() > self.expires_at
    
    def refresh(self):
        from datetime import datetime, timedelta
        self.expires_at = datetime.utcnow() + timedelta(seconds=self.TOKEN_EXPIRY)

# File: src/services/auth.py (520 lines)
class AuthService:
    def __init__(self, db, cache):
        self.db = db
        self.cache = cache
    
    def authenticate(self, email, password):
        user = self.db.query(User).filter_by(email=email).first()
        if not user:
            return None
        if not self._verify_password(password, user.password_hash):
            return None
        session = self._create_session(user)
        self.cache.set(f"session:{session.token}", user.id, ttl=3600)
        return session
    
    def _verify_password(self, password, hash):
        import bcrypt
        return bcrypt.checkpw(password.encode(), hash.encode())
    
    def _create_session(self, user):
        import secrets
        token = secrets.token_hex(32)
        session = Session(
            user_id=user.id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(seconds=Session.TOKEN_EXPIRY),
            ip_address=None,
            user_agent=None
        )
        self.db.add(session)
        self.db.commit()
        return session
    
    def logout(self, token):
        self.cache.delete(f"session:{token}")
        self.db.query(Session).filter_by(token=token).delete()
        self.db.commit()

# File: src/services/permission.py (280 lines)
class PermissionService:
    ROLES = {
        "admin": ["read", "write", "delete", "manage_users", "manage_settings"],
        "editor": ["read", "write"],
        "viewer": ["read"],
    }
    
    def check_permission(self, user, resource, action):
        required = f"{action}:{resource}"
        return required in self.ROLES.get(user.role, [])
    
    def grant_permission(self, user, permission):
        user.role.permissions.append(permission)
        self.db.commit()

# File: src/api/routes.py (650 lines)
from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    session = auth_service.authenticate(data['email'], data['password'])
    if not session:
        return jsonify({"error": "Invalid credentials"}), 401
    return jsonify({"token": session.token, "user": session.user.to_dict()})

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    token = request.headers.get('Authorization')
    session = session_service.validate(token)
    if not session:
        return jsonify({"error": "Unauthorized"}), 401
    user = db.query(User).get(user_id)
    if not user:
        return jsonify({"error": "Not found"}), 404
    return jsonify(user.to_dict())

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.json
    if not auth_service.current_user.has_permission('manage_users'):
        return jsonify({"error": "Forbidden"}), 403
    user = User(
        name=data['name'],
        email=data['email'],
        role=Role(name=data.get('role', 'viewer'))
    )
    db.add(user)
    db.commit()
    return jsonify(user.to_dict()), 201

# File: src/utils/crypto.py (180 lines)
def hash_password(password):
    import bcrypt
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def generate_token():
    import secrets
    return secrets.token_hex(32)

def verify_token(token, secret):
    import hmac
    return hmac.compare_digest(token, secret)

# File: src/utils/cache.py (200 lines)
class RedisCache:
    def __init__(self, redis_client):
        self.client = redis_client
    
    def get(self, key):
        return self.client.get(key)
    
    def set(self, key, value, ttl=None):
        if ttl:
            self.client.setex(key, ttl, value)
        else:
            self.client.set(key, value)
    
    def delete(self, key):
        self.client.delete(key)

# File: src/middleware/auth.py (150 lines)
def require_auth(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": "No token provided"}), 401
        session = session_service.validate(token)
        if not session or session.is_expired():
            return jsonify({"error": "Invalid or expired token"}), 401
        request.current_user = session.user
        return f(*args, **kwargs)
    return decorated

# File: src/middleware/rate_limit.py (100 lines)
from functools import wraps
def rate_limit(max_requests=100, window=60):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            key = f"rate:{request.remote_addr}"
            count = cache.get(key)
            if count and int(count) >= max_requests:
                return jsonify({"error": "Rate limit exceeded"}), 429
            cache.set(key, (int(count or 0) + 1), ttl=window)
            return f(*args, **kwargs)
        return decorated
    return decorator

# File: tests/test_auth.py (300 lines)
import pytest
from src.services.auth import AuthService
from src.models.user import User

class TestAuthService:
    def setup_method(self):
        self.auth = AuthService(db=MockDB(), cache=MockCache())
    
    def test_authenticate_success(self):
        user = User(id=1, name="Test", email="test@example.com", role=Role(name="admin"))
        session = self.auth.authenticate("test@example.com", "password123")
        assert session is not None
        assert session.user.id == 1
    
    def test_authenticate_wrong_password(self):
        session = self.auth.authenticate("test@example.com", "wrong")
        assert session is None
    
    def test_authenticate_nonexistent_user(self):
        session = self.auth.authenticate("nonexistent@example.com", "password123")
        assert session is None

# File: requirements.txt (20 lines)
flask==3.0.0
bcrypt==4.1.2
redis==5.0.1
pytest==8.0.0
sqlalchemy==2.0.23

# File: Dockerfile (25 lines)
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ ./src/
EXPOSE 5000
CMD ["python", "-m", "src.api.routes"]

# File: .env.example (15 lines)
DATABASE_URL=postgresql://localhost:5432/myapp
REDIS_URL=redis://localhost:6379
SECRET_KEY=change-me
SESSION_EXPIRY=3600
MAX_TOKENS=1000
```

QUESTIONS:
1. What is the constant `TOKEN_EXPIRY` set to in the Session class, and where is it also used?
2. Which middleware function protects routes, and what does it return if the token is expired?
3. How many files are in this codebase? List them.
4. What is the rate limit default (max_requests and window) in the rate_limit middleware?
5. In the `create_user` route, what permission is checked, and what is the default role assigned if none is provided?
6. What validation does the User class perform on email, and how?

Answer each question concisely, referencing the specific file and class/function."""
    },
    {
        "id": "multi-step-reasoning",
        "name": "Multi-Step Reasoning & Planning",
        "description": "Break down a complex task into steps and execute them",
        "weight": 20,
        "prompt": """You are an AI agent helping debug a production incident. Here's the scenario:

**Incident Report:**
- Production API started returning 500 errors at 2:00 AM UTC
- Users are seeing "Internal Server Error" on the login endpoint
- The database connection pool is exhausted
- Redis cache is returning "OOM command not allowed" errors
- The application logs show: "ConnectionPool exhausted: max_connections=20, active_connections=20, waiting_connections=5"

**Your task:**
1. Identify the root cause chain (what led to what)
2. Propose a 3-step fix plan with specific commands/code changes
3. Explain the relationship between the database connection pool exhaustion and the Redis OOM error
4. How would you prevent this from happening again? Give 3 specific preventive measures with implementation details.

Provide your analysis in a structured format with clear sections. Be specific — don't just say "scale the database." Give actual parameters, configurations, and code changes."""
    },
    {
        "id": "code-generation",
        "name": "Code Generation & Refactoring",
        "description": "Generate complex code with specific requirements",
        "weight": 20,
        "prompt": """Write a complete Python module for a rate-limiting middleware that:

1. Uses a sliding window algorithm (not fixed window)
2. Supports multiple rate limits per user/endpoint combination
3. Stores rate limit data in Redis with atomic operations
4. Handles concurrent requests correctly (no race conditions)
5. Returns appropriate HTTP 429 responses with retry-after headers
6. Supports configuration per user tier (free, pro, enterprise)
7. Includes a decorator interface for easy integration with Flask
8. Has comprehensive error handling

Requirements:
- Must be production-ready, not a toy implementation
- Use Redis EVAL for Lua scripts (atomic operations)
- Include proper type hints
- Include docstrings
- Handle Redis connection failures gracefully (fail open, not closed)
- Include a cleanup mechanism for expired entries

Write the complete module with all necessary imports, classes, and functions. No placeholders. No TODOs. Full implementation."""
    },
    {
        "id": "tool-use-structured",
        "name": "Tool Use & Structured Output",
        "description": "Generate structured JSON output for API integration",
        "weight": 15,
        "prompt": """You are an API integration assistant. Given the following API documentation, generate a complete integration module that handles all endpoints, error cases, and authentication.

API Documentation:
- Base URL: https://api.example.com/v2
- Authentication: Bearer token (passed via Authorization header)
- Endpoints:
  - GET /users — List users (query params: page, limit, sort, filter)
  - POST /users — Create user (body: {name, email, role, metadata})
  - GET /users/:id — Get user by ID
  - PUT /users/:id — Update user (body: partial user object)
  - DELETE /users/:id — Delete user (requires admin role)
  - POST /users/:id/verify — Verify user email (body: {token})
  - GET /users/:id/activity — Get user activity log (query params: start_date, end_date)

Error response format:
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {} // optional
  }
}

Generate:
1. A Python module with an `APIClient` class that handles all endpoints
2. A `User` Pydantic model that validates all user data
3. Error handling with retry logic (max 3 retries with exponential backoff)
4. Proper type hints for all methods
5. Usage examples for each endpoint

Output valid Python code only. No markdown code fences needed — just the code."""
    },
    {
        "id": "instruction-following",
        "name": "Instruction Following & Constraints",
        "description": "Follow complex instructions with multiple constraints",
        "weight": 15,
        "prompt": """Write a technical blog post about "Building Resilient Microservices" that follows ALL of these constraints simultaneously:

CONSTRAINTS:
1. Exactly 5 sections (no more, no less)
2. Each section must be between 100-150 words (no less than 100, no more than 150)
3. The first section must contain exactly 3 numbered lists
4. The second section must include a real-world analogy (not a metaphor — an actual company example)
5. The third section must be written as a dialogue between two engineers (Q&A format)
6. The fourth section must use the word "resilience" at least 5 times and the word "failure" at least 3 times
7. The fifth section must include a code snippet in Python (not JavaScript)
8. Every section must have a title that starts with a different letter (A, B, C, D, E in order)
9. The total word count must be between 500-750 words
10. No section can use the word "simply" or "just" more than once

Format the output as:
TITLE: [title]
SECTION 1: [title]
[text]
SECTION 2: [title]
[text]
...etc

Be precise with the constraints. If you violate any constraint, the entire output is invalid."""
    },
    {
        "id": "sustained-attention",
        "name": "Sustained Attention & Long Task",
        "description": "Maintain quality across a long, multi-part task",
        "weight": 10,
        "prompt": """You are helping refactor a large Python project. The project has the following structure:

src/
├── __init__.py
├── main.py (500 lines)
├── models/
│   ├── __init__.py
│   ├── user.py (800 lines)
│   ├── product.py (600 lines)
│   └── order.py (900 lines)
├── services/
│   ├── __init__.py
│   ├── auth.py (700 lines)
│   ├── user_service.py (500 lines)
│   ├── product_service.py (600 lines)
│   └── order_service.py (800 lines)
├── api/
│   ├── __init__.py
│   ├── routes.py (1000 lines)
│   └── middleware.py (400 lines)
├── utils/
│   ├── __init__.py
│   ├── cache.py (300 lines)
│   ├── db.py (500 lines)
│   └── validators.py (200 lines)
└── tests/
    ├── test_user.py (400 lines)
    ├── test_product.py (350 lines)
    └── test_order.py (500 lines)

TASK: For each of the following 5 sub-tasks, provide a detailed answer. Do NOT skip any sub-task.

Sub-task 1: Analyze the user.py model and identify any design patterns used, potential bugs, and suggestions for improvement. Be specific about line numbers and code patterns.

Sub-task 2: The auth.py service has a known issue where session tokens are not properly invalidated on logout. Propose a fix with specific code changes. Explain why the current implementation is broken.

Sub-task 3: The routes.py file has duplicate code in the user and product endpoints. Identify the duplications and propose a refactoring strategy with specific code examples.

Sub-task 4: The cache.py utility doesn't handle Redis connection failures. Write a complete replacement that includes retry logic, circuit breaker pattern, and fallback behavior.

Sub-task 5: Create a comprehensive test plan for the order_service.py. List at least 10 specific test cases with expected outcomes, covering edge cases, error scenarios, and integration points.

Format each sub-task response with a clear header (SUB-TASK 1, SUB-TASK 2, etc.) and be thorough — this is a code review, not a summary."""
    }
]

def generate_report(results):
    """Generate a detailed benchmark report."""
    report = []
    report.append("=" * 60)
    report.append("🧬 PARIDHI MODEL BENCHMARK REPORT")
    report.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 60)
    report.append("")
    
    # Summary table
    report.append("## MODEL COMPARISON SUMMARY")
    report.append("")
    report.append("| Model | Context Window | Active Params | Pricing (in/out per 1M) |")
    report.append("|-------|---------------|---------------|-------------------------|")
    report.append("| Kimi K2.7-Code | 262K | 32B | $0.612 / $3.07 |")
    report.append("| MiMo-V2.5 | 1M | 15B | $0.10 / $0.28 |")
    report.append("")
    
    # Benchmark results
    for result in results:
        test_id = result['test_id']
        test_name = result['test_name']
        report.append(f"## TEST: {test_name}")
        report.append(f"**ID:** {test_id}")
        report.append(f"**Weight:** {result['weight']}%")
        report.append("")
        
        for model_result in result['models']:
            model = model_result['model']
            report.append(f"### {model}")
            report.append(f"- **Response Time:** {model_result['response_time']:.2f}s")
            report.append(f"- **Tokens Used:** {model_result.get('tokens', 'N/A')}")
            report.append(f"- **Status:** {model_result['status']}")
            if model_result.get('quality_score'):
                report.append(f"- **Quality Score:** {model_result['quality_score']}/10")
            report.append("")
            
            if model_result.get('response'):
                response = model_result['response']
                if len(response) > 500:
                    report.append(f"**Response Preview (first 500 chars):**")
                    report.append(response[:500] + "...")
                else:
                    report.append(f"**Full Response:**")
                    report.append(response)
            report.append("")
    
    # Overall comparison
    report.append("=" * 60)
    report.append("## OVERALL COMPARISON")
    report.append("")
    report.append("### For OpenClaw/Hermes Agent Tasks:")
    report.append("")
    report.append("1. **Long Context**: MiMo-V2.5 (1M) vs Kimi K2.7-Code (262K) — MiMo wins on context size")
    report.append("2. **Coding**: Kimi K2.7-Code is code-specialized — likely better at code generation")
    report.append("3. **Cost**: MiMo-V2.5 is ~4-5x cheaper per token")
    report.append("4. **Speed**: Need to measure — MiMo has 2.53s p95 latency")
    report.append("5. **Tool Use**: Both support function calling and structured output")
    report.append("6. **Reasoning**: Both have reasoning modes")
    report.append("")
    report.append("### Recommendation for OpenClaw:")
    report.append("- **For code tasks**: Kimi K2.7-Code (primary)")
    report.append("- **For long-context tasks**: MiMo-V2.5 (1M context)")
    report.append("- **For cost-sensitive**: MiMo-V2.5 (much cheaper)")
    report.append("- **For agent tasks**: Both are good, but MiMo has larger context for multi-turn")
    report.append("")
    
    return "\n".join(report)

def run_benchmark():
    """Run the benchmark suite."""
    results = []
    
    print("🧬 PARIDHI MODEL BENCHMARK")
    print("=" * 60)
    print(f"Tests: {len(TESTS)}")
    print(f"Models: Kimi K2.7-Code, MiMo-V2.5")
    print("=" * 60)
    print()
    
    # Run each test
    for test in TESTS:
        print(f"\n--- Running: {test['name']} ---")
        print(f"ID: {test['id']}")
        print(f"Weight: {test['weight']}%")
        print()
        
        test_result = {
            'test_id': test['id'],
            'test_name': test['name'],
            'weight': test['weight'],
            'models': []
        }
        
        # We'll run this as a sub-agent for each model
        print(f"  Prompt length: {len(test['prompt'])} chars")
        print(f"  Ready to run via OpenClaw sub-agent")
        
        results.append(test_result)
    
    # Generate report
    report = generate_report(results)
    
    # Save report
    report_path = os.path.join(os.path.dirname(__file__), 'results', f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"\nReport saved to: {report_path}")
    print(report)
    
    return results

if __name__ == "__main__":
    run_benchmark()
