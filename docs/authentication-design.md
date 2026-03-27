# Authentication & Authorization Design

**Created:** March 26, 2026  
**Status:** Implemented (Phase 1/2 foundation complete)  
**Feature Branch:** `feature/authentication-authorization`

---

## Overview

This document outlines the authentication and authorization strategy for the Quality Metrics Platform API.

## Current Implementation Snapshot (March 27, 2026)

- ✅ `api_keys` schema + ORM model implemented
- ✅ Auth service implemented (`src/services/auth_service.py`)
- ✅ Auth dependencies implemented (`src/dependencies/auth.py`)
- ✅ Admin API key endpoints implemented (`src/routers/admin.py`)
- ✅ Admin router wired in `src/main.py`
- ✅ Test coverage:
  - `tests/unit/test_auth_service.py` (16 tests)
  - `tests/unit/test_auth_dependencies.py` (12 tests)
  - `tests/component/test_api_key_endpoints.py` (13 tests)
  - `src/dependencies/auth.py`: 100% coverage

## Requirements

### Functional
- Secure API access using API keys
- Team-based data isolation (teams can only access their own metrics)
- API key lifecycle management (create, revoke, rotate)
- Support for admin keys (cross-team access for dashboards)
- Rate limiting per API key (future enhancement)

### Non-Functional
- Minimal performance impact on existing endpoints
- Backward compatibility during migration (optional grace period)
- Secure key storage (hashed, never stored in plaintext)
- Simple integration with existing FastAPI dependency injection

---

## Authentication Strategy

### API Key Authentication

**Method:** Bearer token in `Authorization` header

```http
Authorization: Bearer qmp_1234567890abcdef...
```

**Key Format:**
- Prefix: `qmp_` (Quality Metrics Platform)
- Length: 32 characters (hex) after prefix
- Example: `qmp_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`

**Key Storage:**
- Store SHA-256 hash of the key in database
- Never store plaintext keys
- Return plaintext key only once during creation

---

## Authorization Strategy

### Team-Based Access Control

**Principles:**
1. Each API key belongs to a team
2. Teams can only access their own projects and metrics
3. Admin keys can access all teams (for dashboards/reporting)

**Access Rules:**

| Endpoint | Required Permission | Notes |
|----------|-------------------|-------|
| `POST /api/v1/deployments` | Team member | Auto-creates projects under team |
| `POST /api/v1/defects` | Team member | Team-scoped |
| `POST /api/v1/coverage` | Team member | Team-scoped |
| `GET /api/v1/dora-metrics` | Team member or Admin | Filter by team unless admin |
| `GET /api/v1/defect-trends` | Team member or Admin | Filter by team unless admin |
| `GET /api/v1/coverage-trends` | Team member or Admin | Filter by team unless admin |
| `GET /health` | Public | No auth required |
| `POST /api/v1/api-keys` | Admin only | Key management |
| `GET /api/v1/api-keys` | Admin only | List all keys |
| `DELETE /api/v1/api-keys/{id}` | Admin only | Revoke keys |

---

## Database Schema Changes

### New Table: `api_keys`

```sql
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    key_name VARCHAR(100) NOT NULL,
    key_hash VARCHAR(64) NOT NULL UNIQUE,  -- SHA-256 hash
    is_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,
    revoked_at TIMESTAMP,
    created_by VARCHAR(100)  -- Username/email for audit
);

CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_team_id ON api_keys(team_id);
CREATE INDEX idx_api_keys_active ON api_keys(is_active) WHERE is_active = TRUE;
```

---

## Implementation Components

### 1. Database Models (`src/models/db_models.py`)

```python
class ApiKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"))
    key_name = Column(String(100), nullable=False)
    key_hash = Column(String(64), unique=True, nullable=False)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime)
    revoked_at = Column(DateTime)
    created_by = Column(String(100))
    
    team = relationship("Team", back_populates="api_keys")
```

### 2. Authentication Service (`src/services/auth_service.py`)

**Responsibilities:**
- Generate API keys
- Hash and verify keys
- Update last_used_at timestamp
- Revoke keys

**Key Functions:**
```python
def generate_api_key() -> str
def hash_api_key(key: str) -> str
def verify_api_key(key: str, key_hash: str) -> bool
def create_api_key(db, team_id, key_name, is_admin, created_by) -> tuple[ApiKey, str]
def authenticate(db, api_key: str) -> Optional[ApiKey]
def revoke_api_key(db, key_id: int) -> bool
```

### 3. Authentication Dependency (`src/dependencies/auth.py`)

**FastAPI Dependency:**
```python
async def get_current_api_key(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> ApiKey:
    """Extract and validate API key from Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing or invalid authorization header")
    
    api_key = authorization.replace("Bearer ", "")
    key_obj = authenticate(db, api_key)
    
    if not key_obj or not key_obj.is_active:
        raise HTTPException(401, "Invalid or inactive API key")
    
    return key_obj

async def require_admin(api_key: ApiKey = Depends(get_current_api_key)) -> ApiKey:
    """Require admin API key."""
    if not api_key.is_admin:
        raise HTTPException(403, "Admin access required")
    return api_key
```

### 4. Authorization Middleware

**Team-scoped queries:**
```python
def filter_by_team(query, api_key: ApiKey, team_id: int = None):
    """Apply team filter unless admin key."""
    if api_key.is_admin:
        if team_id:  # Admin can filter by specific team
            return query.filter(Team.id == team_id)
        return query  # Admin sees all
    else:
        return query.filter(Team.id == api_key.team_id)
```

### 5. API Key Management Endpoints (`src/routers/admin.py`)

```python
POST /api/v1/api-keys          # Create new API key (admin only)
GET /api/v1/api-keys           # List all API keys (admin only)
DELETE /api/v1/api-keys/{id}   # Revoke API key (admin only)
```

### 6. Updated Metric Endpoints

**Add authentication dependency:**
```python
@router.post("/deployments")
async def create_deployment(
    deployment: DeploymentCreate,
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key)  # NEW
):
    # Verify project belongs to API key's team
    # ...
```

---

## Migration Strategy

### Phase 1: Additive (No Breaking Changes)
1. Add `api_keys` table to schema
2. Implement auth service and dependencies
3. Add API key management endpoints
4. Make auth **optional** on existing endpoints (check for header, don't require)

### Phase 2: Enforcement (Breaking Change)
1. Update all metric endpoints to require authentication
2. Document migration guide for users
3. Provide sample API key creation scripts
4. Set deprecation timeline for unauthenticated access

### Phase 3: Cleanup
1. Remove optional auth code
2. Add rate limiting
3. Add API key rotation

---

## Security Considerations

1. **Key Storage:** SHA-256 hashing (one-way, cannot retrieve plaintext)
2. **Key Transmission:** HTTPS only in production
3. **Key Generation:** Cryptographically secure random (secrets.token_hex)
4. **Audit Trail:** Track created_by, created_at, last_used_at, revoked_at
5. **Revocation:** Soft delete (is_active flag) + optional hard delete

---

## Testing Strategy

### Unit Tests
- `test_auth_service.py`: Key generation, hashing, verification
- `test_auth_dependencies.py`: Header parsing, authentication logic

### Integration Tests
- `test_api_key_management.py`: CRUD operations on API keys
- `test_protected_endpoints.py`: Auth enforcement on metric endpoints
- `test_team_isolation.py`: Verify team-scoped data access

> Current implementation includes equivalent component and unit coverage in:
> - `tests/component/test_api_key_endpoints.py`
> - `tests/unit/test_auth_service.py`
> - `tests/unit/test_auth_dependencies.py`

### Component Tests
- Update existing tests to use API keys
- Test admin vs team member access

---

## API Documentation Updates

### Request Examples

**Create API Key:**
```bash
curl -X POST http://localhost:8000/api/v1/api-keys \
  -H "Authorization: Bearer qmp_admin_key" \
  -H "Content-Type: application/json" \
  -d '{
    "team_id": 1,
    "key_name": "CI/CD Integration",
    "is_admin": false,
    "created_by": "admin@example.com"
  }'
```

**Use API Key:**
```bash
curl -X POST http://localhost:8000/api/v1/deployments \
  -H "Authorization: Bearer qmp_a1b2c3d4..." \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "API Gateway",
    "deployment_status": "success",
    ...
  }'
```

---

## Performance Impact

**Expected Overhead:**
- Database lookup: 1 additional query per request (api_keys table)
- SHA-256 verification: ~1ms
- Mitigation: Index on key_hash, consider caching active keys

**Optimization (Future):**
- Cache API key objects (Redis, 5-minute TTL)
- Lazy load team relationship

---

## Rollout Plan

### Week 1: Implementation
- [x] Database schema migration
- [x] Auth service implementation
- [x] API key management endpoints
- [x] Unit tests

### Week 2: Integration
- [ ] Update metric endpoints (optional/required auth as rollout decision)
- [x] Integration/component tests for auth endpoints and flows
- [x] Documentation updates

### Week 3: Deployment
- [ ] Deploy to staging
- [ ] Create initial API keys for test teams
- [ ] Validate team isolation

### Week 4: Enforcement
- [ ] Make auth mandatory
- [ ] Monitor for auth failures
- [ ] Support team onboarding

---

## Future Enhancements

1. **Rate Limiting:** Per-key request limits
2. **Key Rotation:** Scheduled rotation with grace period
3. **Scoped Permissions:** Fine-grained access (read-only, write-only)
4. **OAuth2 Support:** For human users (Grafana dashboards)
5. **Audit Logging:** Track all authenticated requests

---

## References

- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [OWASP API Security](https://owasp.org/www-project-api-security/)
- [API Key Best Practices](https://cloud.google.com/endpoints/docs/openapi/when-why-api-key)

---

**Status:** Authentication foundation implemented and validated  
**Next Steps:** Enforce auth on metric ingestion/retrieval endpoints and finalize team-scoped filtering for all reads