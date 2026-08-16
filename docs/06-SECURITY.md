# Security Design

> **Documento storico (gennaio 2026), superato il 2026-08-16.** Il progetto
> non viene implementato: vedi [ARC-002](architecture/ARC-002.closure-decision.md)
> e lo [spike sui guardrail MCP](09-SPIKE-MCP-GUARDRAILS.md).


## Threat Model

### In Scope

| Threat | Severity | Mitigation |
|--------|----------|------------|
| **Path Traversal** | HIGH | Sandbox validation, resolve absolute paths |
| **Accidental Deletion** | MEDIUM | Confirmation prompts, audit logging |
| **Large File DoS** | LOW | File size limits (10MB default) |
| **Symlink Exploitation** | MEDIUM | Resolve symlinks, validate final path |

### Out of Scope

| Threat | Reason |
|--------|--------|
| Network Attacks | Local-only tool, no network exposure |
| Code Execution | LLM doesn't execute arbitrary code |
| Data Exfiltration | No network access, local filesystem only |
| Authentication | Single-user local tool |

## Security Architecture

### Defense in Depth (5 Layers)

```
Layer 1: Path Validation
   ↓ Reject malformed paths, relative paths with ..
Layer 2: Sandbox Enforcement
   ↓ Restrict to ALLOWED_PATHS
Layer 3: Permission Checks
   ↓ Verify read/write/execute permissions
Layer 4: Confirmation Prompts
   ↓ User approval for destructive operations
Layer 5: Audit Logging
   ↓ Forensic trail of all filesystem operations
```

## Path Validation Algorithm

```python
async def validate_path(
    path: str,
    allowed_paths: list[Path],
    require_exists: bool = False
) -> Path:
    """
    Validate path is safe and within sandbox.

    Raises:
        InvalidPathError: Path is malformed
        SecurityError: Path outside allowed sandbox
        FileNotFoundError: Path doesn't exist (if require_exists=True)
    """
    # Step 1: Expand user home directory
    expanded = Path(path).expanduser()

    # Step 2: Resolve to absolute path (follows symlinks)
    try:
        resolved = expanded.resolve(strict=require_exists)
    except Exception as e:
        raise InvalidPathError(f"Cannot resolve path '{path}': {e}")

    # Step 3: Check if within any allowed base path
    for allowed_base in allowed_paths:
        allowed_resolved = allowed_base.resolve()
        try:
            # This raises ValueError if resolved is not relative to allowed_base
            resolved.relative_to(allowed_resolved)

            # Path is within allowed base - success!
            if require_exists and not resolved.exists():
                raise FileNotFoundError(f"Path does not exist: {resolved}")

            logger.debug(f"Path validated: {resolved} (within {allowed_base})")
            return resolved

        except ValueError:
            continue  # Try next allowed base

    # No allowed base matched
    raise SecurityError(
        f"Path '{resolved}' is outside allowed paths: {allowed_paths}"
    )
```

## Security Tests

### Adversarial Path Inputs

```python
@pytest.mark.parametrize("malicious_path,description", [
    ("../../etc/passwd", "Parent directory traversal"),
    ("/etc/passwd", "Absolute path outside sandbox"),
    ("~/../../etc/passwd", "Home + traversal"),
    ("projects/../../../etc/passwd", "Mixed relative/absolute"),
    ("projects/./.././../etc/passwd", "Hidden traversal"),
    ("/tmp/link_to_etc", "Symlink to sensitive directory"),
])
async def test_path_traversal_blocked(malicious_path: str, description: str):
    """Verify all path traversal attacks are blocked."""
    config = OrchestratorConfig(allowed_paths=[Path.home() / "projects"])

    with pytest.raises(SecurityError, match="outside allowed paths"):
        await validate_path(malicious_path, config.allowed_paths)
```

### File Size Limits

```python
async def test_large_file_rejected():
    """Verify files exceeding size limit are rejected."""
    # Create 11MB file (exceeds 10MB default limit)
    large_file = tmp_path / "large.bin"
    large_file.write_bytes(b"x" * (11 * 1024 * 1024))

    with pytest.raises(FileTooLargeError, match="exceeds.*10.*MB"):
        await fs_read_file(str(large_file))
```

## Audit Trail

### Audit Log Format (JSONL)

```json
{
  "timestamp": "2026-01-21T10:30:00.123Z",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "action": "write",
  "tool": "fs_write_file",
  "path": "/Users/claudio/projects/test.py",
  "user": "claudio",
  "success": true,
  "error": null,
  "execution_time_ms": 12.5,
  "metadata": {
    "size_bytes": 1024,
    "overwrite": true
  }
}
```

### Audit Events

| Event | Logged | Reason |
|-------|--------|--------|
| `fs_read_file` | Optional (default: No) | Too verbose for normal use |
| `fs_write_file` | Always | Destructive operation |
| `fs_delete` | Always | Destructive operation |
| `fs_move` | Always | Destructive operation |
| `fs_copy` | Always | Creates new files |
| `fs_create_directory` | Always | Modifies filesystem |
| `fs_list_directory` | Optional | Read-only |
| `fs_search` | Optional | Read-only |
| `fs_file_info` | Optional | Read-only |

**Configuration**:
```yaml
# ~/.ollama-fs/config.yaml
audit:
  log_reads: false        # Log read operations
  log_path: ~/.ollama-fs/audit.jsonl
  rotation_size_mb: 100   # Rotate at 100MB
```

## Confirmation Prompts

### Required Confirmations

```python
# 1. Deleting non-empty directory
if path.is_dir() and any(path.iterdir()) and not args.force:
    items = len(list(path.iterdir()))
    if not await prompt_confirmation(
        f"Delete non-empty directory '{path}' ({items} items)?"
    ):
        return "Operation cancelled by user"

# 2. Overwriting large file
if path.exists() and path.stat().st_size > 1_000_000 and not args.overwrite:
    size_mb = path.stat().st_size / (1024 * 1024)
    if not await prompt_confirmation(
        f"Overwrite existing file '{path}' ({size_mb:.1f} MB)?"
    ):
        return "Operation cancelled by user"

# 3. Moving/copying many files
if file_count > 100:
    if not await prompt_confirmation(
        f"About to process {file_count} files. Continue?"
    ):
        return "Operation cancelled by user"
```

## Sandboxing Configuration

### Default Sandbox

```yaml
# ~/.ollama-fs/config.yaml
allowed_paths:
  - ~/projects         # User's project directory
  - ~/documents        # Optional: documents
  # NOT /etc, /var, /usr, /System, etc.
```

### Recommended Practices

1. **Minimal Permissions**: Grant access only to necessary directories
2. **Explicit Paths**: Use absolute paths, not wildcards
3. **No System Directories**: Never allow /etc, /var, /usr, /System
4. **Audit Review**: Regularly review audit.jsonl for suspicious activity

### macOS-Specific Protections

```python
# Block access to sensitive macOS directories
BLOCKED_PATHS = [
    Path("/System"),
    Path("/Library"),
    Path("/usr"),
    Path("/bin"),
    Path("/sbin"),
    Path("/etc"),
    Path("/var"),
    Path("/private"),
]

for blocked in BLOCKED_PATHS:
    if resolved.is_relative_to(blocked):
        raise SecurityError(f"Access to system directory denied: {blocked}")
```

## Encryption

### Data at Rest

**Not Implemented** (out of scope for v0.1.0)

Rationale:
- Local tool, not cloud service
- User controls physical machine security
- macOS FileVault / Linux LUKS provide full-disk encryption

### Data in Transit

**Not Applicable**

- No network communication (Ollama runs locally)
- MCP protocol uses stdio (no network)

## Compliance

**Not Applicable** for v0.1.0

- No PII processing
- No GDPR/HIPAA requirements (local tool)
- Open-source project, not SaaS

## Security Incident Response

### If Security Vulnerability Discovered

1. **Report**: Open GitHub Security Advisory (private disclosure)
2. **Triage**: Assess severity (Low/Medium/High/Critical)
3. **Fix**: Develop patch in private fork
4. **Test**: Verify fix with security tests
5. **Release**: Publish security advisory + patched version
6. **Notify**: Announce on GitHub Discussions

### Security Contact

Report vulnerabilities privately via GitHub Security Advisories:
https://github.com/USER/ollama-mcp-orchestrator/security/advisories

**Do not** open public issues for security vulnerabilities.
