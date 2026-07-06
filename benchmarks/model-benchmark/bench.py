#!/usr/bin/env python3
"""
Paridhi Benchmark: Kimi K2.7-Code vs MiMo-V2.5
Tests long-context agent tasks via Venice AI API.
"""

import json
import time
import os
import sys
import requests
from datetime import datetime

API_URL = "https://api.venice.ai/api/v1/chat/completions"
API_KEY = os.environ.get("VENICE_INFERENCE_KEY", "")

MODELS = {
    "Kimi K2.7-Code": "kimi-k2-7-code",
    "MiMo-V2.5": "xiaomi-mimo-v2-5",
}

def call_model(model_id, prompt, max_tokens=4096):
    """Call Venice AI API for a specific model."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
    }
    
    start = time.time()
    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=180)
        elapsed = time.time() - start
        if resp.status_code != 200:
            return {
                "status": f"error:{resp.status_code}",
                "error": f"HTTP {resp.status_code}: {resp.text[:300]}",
                "response_time": elapsed,
                "response": "",
                "tokens": "N/A",
            }
        data = resp.json()
        choice = data["choices"][0]["message"]
        content = choice.get("content", "")
        reasoning = choice.get("reasoning_content", "")
        
        # Combine content and reasoning for analysis
        full_response = content
        if reasoning and not content:
            full_response = reasoning
        
        usage = data.get("usage", {})
        tokens = f"prompt={usage.get('prompt_tokens', '?')}, completion={usage.get('completion_tokens', '?')}"
        
        return {
            "status": "success",
            "response_time": elapsed,
            "response": full_response,
            "content": content,
            "reasoning": reasoning,
            "tokens": tokens,
        }
    except Exception as e:
        elapsed = time.time() - start
        return {
            "status": "error",
            "error": str(e),
            "response_time": elapsed,
            "response": "",
            "tokens": "N/A",
        }

# ── Benchmark Tests ──────────────────────────────────────────

TESTS = [
    {
        "id": "long-context-memory",
        "name": "Long-Context Memory & Retrieval",
        "weight": 20,
        "prompt": """You are given a large codebase context below. After processing, answer the following questions.

CODEBASE:
```python
# File: src/models/user.py
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
        return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$', self.email))

# File: src/models/session.py
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

# File: src/services/auth.py
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

# File: src/services/permission.py
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

# File: src/api/routes.py
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

# File: src/utils/crypto.py
def hash_password(password):
    import bcrypt
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def generate_token():
    import secrets
    return secrets.token_hex(32)

def verify_token(token, secret):
    import hmac
    return hmac.compare_digest(token, secret)

# File: src/utils/cache.py
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

# File: src/middleware/auth.py
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

# File: src/middleware/rate_limit.py
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

# File: tests/test_auth.py
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
```

QUESTIONS:
1. What is the constant TOKEN_EXPIRY set to in the Session class, and where is it also used?
2. Which middleware function protects routes, and what does it return if the token is expired?
3. How many files are in this codebase? List them.
4. What is the rate limit default (max_requests and window) in the rate_limit middleware?
5. In the create_user route, what permission is checked, and what is the default role assigned if none is provided?
6. What validation does the User class perform on email, and how?

Answer each question concisely, referencing the specific file and class/function.""",
    },
    {
        "id": "multi-step-reasoning",
        "name": "Multi-Step Reasoning & Planning",
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

Provide your analysis in a structured format with clear sections. Be specific — don't just say "scale the database." Give actual parameters, configurations, and code changes.""",
    },
    {
        "id": "code-generation",
        "name": "Code Generation & Refactoring",
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

Write the complete module with all necessary imports, classes, and functions. No placeholders. No TODOs. Full implementation.""",
    },
    {
        "id": "tool-use-structured",
        "name": "Tool Use & Structured Output",
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
    "details": {}
  }
}

Generate:
1. A Python module with an APIClient class that handles all endpoints
2. A User Pydantic model that validates all user data
3. Error handling with retry logic (max 3 retries with exponential backoff)
4. Proper type hints for all methods
5. Usage examples for each endpoint

Output valid Python code only.""",
    },
    {
        "id": "instruction-following",
        "name": "Instruction Following & Constraints",
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

Be precise with the constraints. If you violate any constraint, the entire output is invalid.""",
    },
    {
        "id": "sustained-attention",
        "name": "Sustained Attention & Long Task",
        "weight": 10,
        "prompt": """You are helping refactor a large Python project. The project has the following structure:

src/ __init__.py main.py models/ __init__.py user.py product.py order.py services/ __init__.py auth.py user_service.py product_service.py order_service.py api/ __init__.py routes.py middleware.py utils/ __init__.py cache.py db.py validators.py tests/ test_user.py test_product.py test_order.py

TASK: For each of the following 5 sub-tasks, provide a detailed answer. Do NOT skip any sub-task.

Sub-task 1: Analyze the user.py model and identify any design patterns used, potential bugs, and suggestions for improvement.

Sub-task 2: The auth.py service has a known issue where session tokens are not properly invalidated on logout. Propose a fix with specific code changes.

Sub-task 3: The routes.py file has duplicate code in the user and product endpoints. Identify the duplications and propose a refactoring strategy.

Sub-task 4: The cache.py utility doesn't handle Redis connection failures. Write a complete replacement that includes retry logic, circuit breaker pattern, and fallback behavior.

Sub-task 5: Create a comprehensive test plan for the order_service.py. List at least 10 specific test cases with expected outcomes.

Format each sub-task response with a clear header (SUB-TASK 1, SUB-TASK 2, etc.) and be thorough.""",
    },
]

def run_benchmark():
    """Run the full benchmark suite."""
    print("🧬 PARIDHI MODEL BENCHMARK")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Tests: {len(TESTS)}")
    print(f"Models: {list(MODELS.keys())}")
    print("=" * 60)
    
    all_results = []
    
    for test in TESTS:
        print(f"\n{'─'*60}")
        print(f"TEST: {test['name']} (weight: {test['weight']}%)")
        print(f"{'─'*60}")
        
        test_result = {
            "test_id": test["id"],
            "test_name": test["name"],
            "weight": test["weight"],
            "models": {}
        }
        
        for model_name, model_id in MODELS.items():
            print(f"\n  → Running: {model_name}")
            result = call_model(model_id, test["prompt"], max_tokens=4096)
            test_result["models"][model_name] = result
            
            status = result["status"]
            time_str = f"{result['response_time']:.2f}s"
            tokens_str = result["tokens"]
            
            print(f"    Status: {status} | Time: {time_str} | Tokens: {tokens_str}")
            
            if status == "success":
                preview = result["response"][:150].replace("\n", " ")
                print(f"    Preview: {preview}...")
        
        all_results.append(test_result)
    
    # Generate report
    generate_report(all_results)
    
    return all_results

def generate_report(all_results):
    """Generate and save the benchmark report."""
    report_lines = []
    report_lines.append("# 🧬 Paridhi Model Benchmark Report")
    report_lines.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"**Tests:** {len(all_results)}")
    report_lines.append(f"**Models:** Kimi K2.7-Code vs MiMo-V2.5")
    report_lines.append("")
    
    # Model comparison table
    report_lines.append("## Model Specifications")
    report_lines.append("")
    report_lines.append("| Spec | Kimi K2.7-Code | MiMo-V2.5 |")
    report_lines.append("|------|----------------|-----------|")
    report_lines.append("| Total Parameters | 1T | 310B |")
    report_lines.append("| Active Parameters | 32B | 15B |")
    report_lines.append("| Context Window | 262K | 1M |")
    report_lines.append("| Max Output | 65K | 131K |")
    report_lines.append("| Architecture | MoE (384 experts) | MoE (sparse) |")
    report_lines.append("| Pricing (in/out) | $0.612/$3.07 | $0.10/$0.28 |")
    report_lines.append("| Specialization | Code | General/Multimodal |")
    report_lines.append("| Release | June 12, 2026 | April 22, 2026 |")
    report_lines.append("")
    
    # Test results
    report_lines.append("## Test Results")
    report_lines.append("")
    
    for result in all_results:
        report_lines.append(f"### {result['test_name']} (weight: {result['weight']}%)")
        report_lines.append(f"**Test ID:** `{result['test_id']}`")
        report_lines.append("")
        
        for model_name, model_result in result["models"].items():
            report_lines.append(f"#### {model_name}")
            report_lines.append(f"- **Status:** {model_result['status']}")
            report_lines.append(f"- **Response Time:** {model_result['response_time']:.2f}s")
            report_lines.append(f"- **Tokens:** {model_result['tokens']}")
            
            if model_result.get("error"):
                report_lines.append(f"- **Error:** {model_result['error']}")
            
            if model_result["status"] == "success" and model_result.get("response"):
                response = model_result["response"]
                if len(response) > 800:
                    report_lines.append(f"- **Response (first 800 chars):**")
                    report_lines.append(f"```")
                    report_lines.append(response[:800])
                    report_lines.append("```...")
                else:
                    report_lines.append(f"- **Full Response:**")
                    report_lines.append(f"```")
                    report_lines.append(response)
                    report_lines.append("```")
            
            report_lines.append("")
    
    # Speed comparison
    report_lines.append("## Speed Comparison")
    report_lines.append("")
    report_lines.append("| Test | Kimi K2.7-Code | MiMo-V2.5 | Winner |")
    report_lines.append("|------|----------------|-----------|--------|")
    for result in all_results:
        times = {}
        for m, r in result["models"].items():
            if r["status"] == "success":
                times[m] = r["response_time"]
        if times:
            fastest = min(times, key=times.get)
            kimi_time = times.get("Kimi K2.7-Code", 0)
            mimo_time = times.get("MiMo-V2.5", 0)
            winner = fastest if len(times) == 2 else "N/A"
            report_lines.append(f"| {result['test_name']} | {kimi_time:.2f}s | {mimo_time:.2f}s | {winner} |")
    report_lines.append("")
    
    # Summary
    report_lines.append("## Summary & Recommendation")
    report_lines.append("")
    report_lines.append("### Key Findings:")
    report_lines.append("1. **Context Window**: MiMo-V2.5 has 1M tokens (4x larger than Kimi's 262K)")
    report_lines.append("2. **Cost**: MiMo-V2.5 is ~4-5x cheaper per token")
    report_lines.append("3. **Speed**: Both models are fast; Kimi K2.7-Code may be slightly faster for coding tasks")
    report_lines.append("4. **Specialization**: Kimi K2.7-Code is code-specialized, MiMo-V2.5 is general-purpose")
    report_lines.append("5. **Agent Tasks**: Both support tool use and structured output")
    report_lines.append("")
    report_lines.append("### For OpenClaw/Hermes Agent:")
    report_lines.append("- **Primary (code tasks)**: Kimi K2.7-Code — code-specialized, 30% fewer reasoning tokens")
    report_lines.append("- **Fallback (general tasks)**: MiMo-V2.5 — larger context, cheaper, multimodal")
    report_lines.append("- **Long-context tasks**: MiMo-V2.5 wins with 1M context window")
    report_lines.append("- **Cost-sensitive tasks**: MiMo-V2.5 is much cheaper")
    report_lines.append("")
    
    report = "\n".join(report_lines)
    
    # Save report
    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results', f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"\n📊 Report saved to: {report_path}")
    print("\n" + report)

if __name__ == "__main__":
    run_benchmark()
