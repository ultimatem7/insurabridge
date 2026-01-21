# Insurabridge Security Model

## Overview

Insurabridge is designed with security as a foundational principle, not an afterthought. This document describes the security architecture that ensures HIPAA compliance and protects PHI.

---

## Core Security Principles

### 1. Zero Trust for PHI

**No External API Calls**
- All LLM inference runs locally via Ollama
- No PHI ever transmitted to external services
- All processing happens on-device

**Defense in Depth**
- Multiple layers of protection
- Encryption at rest and in transit
- Least privilege access

**Assume Breach Mentality**
- Comprehensive audit logging
- Anomaly detection
- Rapid incident response

### 2. Data Protection

**Encryption at Rest**
```
Algorithm: AES-256-GCM
Key Derivation: Scrypt (N=16384, r=8, p=1)
Storage: SQLCipher encrypted SQLite
Key Management: OS keychain integration
```

**In-Memory Protection**
- Sensitive data cleared after use
- No PHI caching in plain text
- Secure string handling

**Data Classification**
| Level | Examples | Protection |
|-------|----------|------------|
| PHI | Patient name, DOB, MRN | Full encryption, audit logging |
| Sensitive | User credentials, tokens | Encryption, access control |
| Internal | Audit logs, configs | Access control, integrity checks |
| Public | Code tables, documentation | Integrity verification |

---

## Authentication & Authorization

### Authentication

**Password Requirements**
- Minimum 12 characters
- Uppercase, lowercase, digit, special character
- Argon2id hashing (time=3, memory=64MB)
- No password reuse (tracked)

**Token Management**
```
Access Token:
- JWT with HS256 signature
- 15-minute expiration
- Contains: user_id, role, jti (unique ID)

Refresh Token:
- JWT with HS256 signature
- 7-day expiration
- Single use (revoked after refresh)
```

**Session Security**
- Automatic timeout after 15 minutes inactivity
- Secure, httpOnly, sameSite cookies
- Session invalidation on logout
- Device binding (optional)

**Brute Force Protection**
- 5 failed attempts → 30-minute lockout
- Per-user attempt tracking
- Exponential backoff
- Account lockout notification

### Authorization (RBAC)

**Roles**
| Role | Description | Typical User |
|------|-------------|--------------|
| Admin | Full system access | IT Administrator |
| Billing Manager | Claims, appeals, reports | Revenue Cycle Manager |
| Coder | Code validation, claim generation | Medical Coder |
| Auditor | Read-only, audit reports | Compliance Officer |
| Viewer | Dashboard only | Executive, Observer |

**Permission Matrix**
| Permission | Admin | Billing Mgr | Coder | Auditor | Viewer |
|------------|-------|-------------|-------|---------|--------|
| claim:create | ✓ | ✓ | ✓ | | |
| claim:read | ✓ | ✓ | ✓ | ✓ | ✓ |
| claim:update | ✓ | ✓ | ✓ | | |
| claim:submit | ✓ | ✓ | | | |
| denial:appeal | ✓ | ✓ | | | |
| audit:read | ✓ | | | ✓ | |
| audit:export | ✓ | | | ✓ | |
| system:admin | ✓ | | | | |
| user:manage | ✓ | | | | |

---

## Audit Logging

### Design

**Immutable Append-Only Log**
- No update or delete operations
- Cryptographic hash chaining
- Tamper detection on read

**Chain Structure**
```
Entry N:
  - id: unique identifier
  - timestamp: UTC ISO 8601
  - event_type: categorized action
  - user_id: actor (hashed if needed)
  - resource_id: affected resource
  - details: action-specific data
  - previous_hash: SHA-256 of entry N-1
  - entry_hash: SHA-256 of this entry
```

**Verification**
```python
def verify_chain():
    previous_hash = None
    for entry in audit_log:
        # Verify chain link
        assert entry.previous_hash == previous_hash
        
        # Verify entry integrity
        computed = sha256(entry.content)
        assert entry.entry_hash == computed
        
        previous_hash = entry.entry_hash
```

### Logged Events

| Category | Events |
|----------|--------|
| Authentication | login_success, login_failure, logout, token_refresh, password_change |
| User Management | user_create, user_update, user_delete, role_change |
| PHI Access | phi_view, phi_create, phi_update, phi_delete, phi_export |
| Claims | claim_create, claim_update, claim_validate, claim_submit |
| Denials | denial_review, appeal_generate, appeal_submit |
| System | config_change, error, startup, shutdown |

### Retention

- **Minimum:** 7 years (HIPAA requirement)
- **Default:** 2555 days
- **Storage:** Separate encrypted log file
- **Export:** Signed, encrypted archive

---

## Network Security

### Local-Only Architecture
```
┌─────────────────────────────────────────────┐
│                User Device                   │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐ │
│  │ Browser │───▶│ Frontend│───▶│ Backend │ │
│  │         │    │ :3000   │    │ :8000   │ │
│  └─────────┘    └─────────┘    └────┬────┘ │
│                                     │       │
│                              ┌──────▼─────┐ │
│                              │   Ollama   │ │
│                              │   :11434   │ │
│                              └────────────┘ │
│                                             │
│  No external network calls for inference    │
└─────────────────────────────────────────────┘
```

### Port Bindings
| Service | Port | Binding | Notes |
|---------|------|---------|-------|
| Frontend | 3000 | 127.0.0.1 | Local only |
| Backend | 8000 | 127.0.0.1 | Local only |
| Ollama | 11434 | 127.0.0.1 | Local only |

### TLS Configuration
- Local development: HTTP on localhost only
- Production: TLS 1.3 required if network exposed
- Certificate: Let's Encrypt or internal CA

---

## HIPAA Compliance

### Technical Safeguards

| Requirement | Implementation |
|-------------|----------------|
| Access Control | Role-based access, unique user IDs |
| Audit Controls | Immutable audit logging |
| Integrity Controls | Encryption, hash verification |
| Transmission Security | Local-only, TLS for any network |
| Encryption | AES-256-GCM at rest |

### Administrative Safeguards

| Requirement | Implementation |
|-------------|----------------|
| Security Officer | Configurable role assignment |
| Workforce Training | Built-in training module (future) |
| Access Management | Self-service with approval workflow |
| Incident Procedures | Audit log analysis, alerting |

### Physical Safeguards

| Requirement | Implementation |
|-------------|----------------|
| Facility Access | N/A (local software) |
| Workstation Security | OS-level controls, session timeout |
| Device Controls | Encrypted storage, secure deletion |

---

## Incident Response

### Detection
1. Audit log anomaly detection
2. Failed login monitoring
3. Unusual access patterns
4. Hash chain verification failures

### Response Procedures
1. **Contain** - Revoke affected credentials
2. **Assess** - Review audit logs
3. **Notify** - Alert security officer
4. **Remediate** - Patch, rotate credentials
5. **Report** - Document and file if required

### Breach Notification
- HIPAA requires notification within 60 days
- Template breach notification included
- Audit log export for forensics

---

## Secure Development

### Code Security
- Static analysis (ruff, mypy)
- Dependency scanning
- No secrets in code
- Input validation on all endpoints

### Dependency Management
- Pinned versions
- Regular updates
- Vulnerability scanning
- Minimal dependencies

### Deployment Security
- Signed installers
- Integrity verification
- Automatic updates (signed)
- Rollback capability

---

## Security Checklist

### Pre-Deployment
- [ ] Change default encryption keys
- [ ] Change default admin password
- [ ] Configure session timeout
- [ ] Review role assignments
- [ ] Test audit log verification
- [ ] Confirm local-only binding

### Regular Maintenance
- [ ] Review audit logs weekly
- [ ] Verify hash chain integrity monthly
- [ ] Update dependencies quarterly
- [ ] Penetration test annually
- [ ] Review user access quarterly

### Incident Response
- [ ] Document incident
- [ ] Preserve audit logs
- [ ] Notify affected parties
- [ ] Conduct root cause analysis
- [ ] Update procedures

