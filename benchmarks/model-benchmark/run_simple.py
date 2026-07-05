#!/usr/bin/env python3
"""Simple benchmark runner - tests one at a time."""
import requests
import json
import time
import sys
import os
from datetime import datetime

API_URL = "https://api.venice.ai/api/v1/chat/completions"
API_KEY = "VENICE_INFERENCE_KEY_eSo1FVcIDqp9rr5CI6LLpLUmq2tu721fEasyCWPmcV"

def call_model(model, prompt, max_tokens=4096):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
    }
    start = time.time()
    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=180)
        elapsed = time.time() - start
        if resp.status_code != 200:
            return {"status": f"error:{resp.status_code}", "time": elapsed, "error": resp.text[:300], "response": ""}
        data = resp.json()
        choice = data["choices"][0]["message"]
        content = choice.get("content", "")
        reasoning = choice.get("reasoning_content", "")
        response = content or reasoning
        usage = data.get("usage", {})
        tokens = f"prompt={usage.get('prompt_tokens', '?')}, completion={usage.get('completion_tokens', '?')}"
        return {"status": "success", "time": elapsed, "response": response, "tokens": tokens}
    except Exception as e:
        return {"status": "error", "time": time.time() - start, "error": str(e), "response": ""}

# Test prompts
tests = [
    ("Long-Context Memory", """You are given a large codebase context below. After processing, answer the following questions.

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

Answer each question concisely, referencing the specific file and class/function."""),
    ("Multi-Step Reasoning", """You are an AI agent helping debug a production incident. Here's the scenario:

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

Provide your analysis in a structured format with clear sections. Be specific."""),
    ("Code Generation", """Write a complete Python module for a rate-limiting middleware that:

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

Write the complete module with all necessary imports, classes, and functions. No placeholders."""),
    ("Instruction Following", """Write a technical blog post about "Building Resilient Microservices" that follows ALL of these constraints simultaneously:

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

Be precise with the constraints."""),
]

print(f"🧬 PARIDHI MODEL BENCHMARK — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)
print(f"Tests: {len(tests)}")
print(f"Models: Kimi K2.7-Code, MiMo-V2.5")
print("=" * 60)

all_results = []

for test_name, test_prompt in tests:
    print(f"\n{'─'*60}")
    print(f"TEST: {test_name}")
    print(f"{'─'*60}")
    
    for model_name, model_id in [("Kimi K2.7-Code", "kimi-k2-7-code"), ("MiMo-V2.5", "xiaomi-mimo-v2-5")]:
        print(f"  → {model_name}...", end=" ", flush=True)
        result = call_model(model_id, test_prompt, max_tokens=4096)
        status = result["status"]
        time_str = f"{result['time']:.2f}s"
        tokens_str = result.get("tokens", "N/A")
        
        print(f"{status} | {time_str} | {tokens_str}")
        
        if status != "success":
            print(f"    Error: {result.get('error', 'unknown')[:200]}")
        else:
            preview = result["response"][:100].replace("\n", " ")
            print(f"    Preview: {preview}...")
        
        all_results.append({
            "test": test_name,
            "model": model_name,
            "status": status,
            "time": result["time"],
            "tokens": tokens_str,
            "response": result["response"],
            "error": result.get("error", "")
        })
        
        time.sleep(2)  # Rate limit buffer

# Generate report
report = []
report.append("# 🧬 Paridhi Model Benchmark Report")
report.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
report.append(f"**Models:** Kimi K2.7-Code vs MiMo-V2.5")
report.append("")
report.append("## Speed Comparison")
report.append("| Test | Kimi K2.7-Code | MiMo-V2.5 |")
report.append("|------|----------------|-----------|")

# Group by test
from collections import defaultdict
by_test = defaultdict(dict)
for r in all_results:
    by_test[r["test"]][r["model"]] = r

for test_name in [t[0] for t in tests]:
    row = f"| {test_name} |"
    for model in ["Kimi K2.7-Code", "MiMo-V2.5"]:
        if model in by_test[test_name]:
            r = by_test[test_name][model]
            if r["status"] == "success":
                row += f" {r['time']:.2f}s |"
            else:
                row += f" error |"
        else:
            row += " N/A |"
    report.append(row)

report.append("")
report.append("## Detailed Results")
for test_name in [t[0] for t in tests]:
    report.append(f"### {test_name}")
    for model in ["Kimi K2.7-Code", "MiMo-V2.5"]:
        if model in by_test[test_name]:
            r = by_test[test_name][model]
            report.append(f"**{model}** — Status: {r['status']}, Time: {r['time']:.2f}s")
            if r["response"]:
                if len(r["response"]) > 600:
                    report.append(f"Response (first 600 chars):")
                    report.append(f"```\n{r['response'][:600]}\n```...")
                else:
                    report.append(f"Response:")
                    report.append(f"```\n{r['response']}\n```")
            report.append("")

report.append("## Recommendation")
report.append("- **Kimi K2.7-Code**: Code-specialized, 262K context, good for code tasks")
report.append("- **MiMo-V2.5**: General-purpose, 1M context, cheaper, multimodal")
report.append("- **For OpenClaw**: Kimi for code, MiMo for general/long-context tasks")
report.append("- **Primary**: Kimi K2.7-Code (code-focused)")
report.append("- **Fallback**: MiMo-V2.5 (general tasks, long context)")

report_text = "\n".join(report)

# Save
report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results', f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
os.makedirs(os.path.dirname(report_path), exist_ok=True)
with open(report_path, 'w') as f:
    f.write(report_text)

print(f"\n📊 Report saved to: {report_path}")
print("\n" + report_text)
