# Requirements Specification

## Functional Requirements

### FR-001: Filesystem Tools

**Priority**: P0 (Critical)

The system must provide 9 core filesystem operation tools:

1. **fs_read_file**: Read file content with size limit (10MB default)
2. **fs_write_file**: Create or overwrite file with content
3. **fs_list_directory**: List directory contents with metadata (recursive option)
4. **fs_create_directory**: Create directory including intermediate directories
5. **fs_delete**: Delete file or directory (with confirmation for non-empty dirs)
6. **fs_move**: Move or rename file/directory
7. **fs_copy**: Copy file or directory
8. **fs_search**: Search files by glob pattern or content match
9. **fs_file_info**: Get detailed file metadata (size, permissions, modified time)

**Acceptance Criteria**:
- All tools accept path parameters as strings
- All tools return structured results (success/error, output, execution time)
- All tools validate paths against ALLOWED_PATHS sandbox
- All destructive operations (write, delete, move) log to audit trail

### FR-002: Agent Loop (ReAct Pattern)

**Priority**: P0 (Critical)

Implement autonomous agent loop with 8 stages:

1. **USER_INPUT**: Receive natural language query
2. **PLANNING**: Ollama analyzes task and decides if tool needed
3. **TOOL_CALL**: Parse JSON tool request and validate arguments
4. **EXECUTION**: Execute MCP tool with timeout
5. **OBSERVATION**: Insert tool result into conversation context
6. **REFLECTION**: Ollama evaluates if task completed
7. **LOOP**: Return to PLANNING if not completed (max 10 iterations)
8. **RESPONSE**: Generate final natural language answer

**Acceptance Criteria**:
- Agent completes 3-step tasks (e.g., search → read → summarize)
- Loop terminates after max_iterations (default: 10)
- Tool call failures don't crash the loop
- Final response includes all intermediate observations

### FR-003: CLI Interface

**Priority**: P0 (Critical)

Provide Typer-based CLI with these commands:

```bash
ollama-fs chat              # Interactive chat mode
ollama-fs ask "query"       # Single query mode
ollama-fs --model llama3.3  # Override default model
ollama-fs --verbose         # Enable debug logging
ollama-fs config show       # Display current configuration
ollama-fs config set KEY VAL # Update configuration value
```

**Acceptance Criteria**:
- `chat` mode supports multi-turn conversations
- `ask` mode returns single response and exits
- `--model` flag validates model exists in Ollama
- `config` commands persist to `~/.ollama-fs/config.yaml`

### FR-004: Security Sandbox

**Priority**: P0 (Critical)

Enforce path-based security sandbox:

- **ALLOWED_PATHS**: Configurable list of allowed base paths (default: `~/projects`)
- **Path Validation**: Resolve all paths with `Path.resolve()` before access
- **Traversal Prevention**: Reject paths containing `..` or absolute paths outside sandbox
- **Confirmation Prompts**: Require user confirmation for:
  - Deleting non-empty directories
  - Overwriting existing files > 1MB
  - Moving/copying > 100 files

**Acceptance Criteria**:
- Attempts to access `/etc/passwd` fail with clear error
- Symlinks outside sandbox are rejected
- Security audit logs all validation failures

### FR-005: Audit Logging

**Priority**: P1 (High)

Log all filesystem operations to JSONL audit file:

```json
{
  "timestamp": "2026-01-21T10:30:00Z",
  "action": "write",
  "tool": "fs_write_file",
  "path": "/Users/claudio/projects/test.py",
  "user": "claudio",
  "session_id": "uuid-xxx",
  "success": true,
  "execution_time_ms": 12.5
}
```

**Acceptance Criteria**:
- All write/delete/move operations logged
- Read operations optionally logged (configurable)
- Log rotation at 100MB file size
- Audit log path configurable via `OLLAMA_FS_AUDIT_LOG`

### FR-006: Ollama Integration

**Priority**: P0 (Critical)

Integrate with Ollama Python client:

- Support models: Qwen2.5:32b, Llama3.3:70b, Qwen3-coder:30b
- Use chat API with function calling
- Handle streaming responses (nice-to-have for v0.2.0)
- Retry failed requests with exponential backoff (3 attempts)

**Acceptance Criteria**:
- Model availability checked at startup
- Invalid model names fail fast with helpful error
- Ollama connection failures retry with backoff

### FR-007: Conversation Management

**Priority**: P2 (Medium)

Maintain conversation state:

- **In-Memory History**: Keep full message history in `AgentState`
- **Context Window**: Truncate to max_context_tokens (default: 32000)
- **Persistence**: Optional save/load conversations to JSON (v0.2.0)

**Acceptance Criteria**:
- Multi-turn conversations reference previous context
- Context truncation preserves system prompt + recent messages
- Saved conversations loadable in future sessions

### FR-008: Error Handling

**Priority**: P1 (High)

Comprehensive error handling:

- **User Errors**: Invalid paths, missing files → actionable error messages
- **System Errors**: Ollama down, permission denied → retry or graceful degradation
- **Timeout Errors**: Long operations → cancel after timeout, report partial results

**Acceptance Criteria**:
- All errors include clear remediation steps
- Stack traces only shown in `--verbose` mode
- Partial results returned when possible (e.g., search timeout after 100 matches)

### FR-009: Configuration Management

**Priority**: P2 (Medium)

Manage configuration via file + env vars:

- **Config File**: `~/.ollama-fs/config.yaml` (Pydantic Settings)
- **Environment Variables**: Override with `OLLAMA_FS_*` prefix
- **CLI Flags**: Override for single session

**Precedence**: CLI flags > Env vars > Config file > Defaults

**Acceptance Criteria**:
- `config show` displays effective config (after precedence)
- `config set` persists to config file
- Invalid config values fail with validation errors

## Non-Functional Requirements

### NFR-001: Performance

**Tool Call Latency**: < 100ms (excluding LLM inference)

Measured as: Tool start → Result returned

**Acceptance Criteria**:
- `fs_read_file` for 1MB file: < 50ms
- `fs_list_directory` for 1000 files: < 100ms
- `fs_search` for 10,000 files: < 2s

### NFR-002: Scalability

**Target**: Single-user, local tool (no multi-user scaling needed)

**Resource Limits**:
- Max file size read: 10MB (configurable)
- Max directory depth: 10 levels
- Max search results: 1000 files

### NFR-003: Availability

**Target**: Local CLI tool, no SLA required

**Graceful Degradation**:
- If MCP server down → clear error, suggest restart
- If Ollama down → clear error, suggest `ollama serve`

### NFR-004: Security

**Level**: Medium (local filesystem access, no network exposure)

**Threat Model**:
- **Path Traversal**: BLOCKED by sandbox validation
- **Arbitrary Code Execution**: NOT IN SCOPE (LLM doesn't execute code)
- **Data Exfiltration**: NOT IN SCOPE (local-only tool)

**Compliance**: None required (open-source project)

### NFR-005: Maintainability

**Code Quality Standards**:
- Type hints on all functions (basedpyright strict mode)
- Docstrings (Google style) on all public APIs
- Unit test coverage > 80% line, > 70% branch
- Ruff linting with strict ruleset

**Acceptance Criteria**:
- `basedpyright .` passes with zero errors
- `ruff check .` passes with zero errors
- `pytest --cov` reports > 80% coverage

### NFR-006: Documentation

**Required Docs**:
- README.md with quickstart (< 5 minutes to first run)
- API reference (auto-generated from docstrings)
- Example gallery (5+ real-world scenarios)
- Security guide (sandbox configuration)

**Acceptance Criteria**:
- New user can install and run first query in < 5 minutes
- All public APIs documented with examples

### NFR-007: Portability

**Platforms**: macOS (Apple Silicon) + Debian Linux

**Python Version**: 3.12+

**Dependencies**: Managed via `uv` (no system packages required)

**Acceptance Criteria**:
- Tests pass on Mac Studio M2 Ultra (macOS Sequoia)
- Tests pass on Debian 12 (x86_64)
- Single `uv` command installs all dependencies

### NFR-008: Testing

**Test Coverage Requirements**:
- Unit tests: > 80% line coverage
- Integration tests: Agent loop end-to-end scenarios
- Security tests: Path traversal, sandbox bypass attempts
- Performance tests: Latency benchmarks for each tool

**Acceptance Criteria**:
- All tests pass on CI (GitHub Actions)
- No flaky tests (3 consecutive runs without failures)
- Security tests include adversarial path inputs

### NFR-009: Logging

**Structured Logging** (Loguru):

```python
logger.bind(
    tool_name="fs_read_file",
    path="/path/to/file",
    user="claudio",
    session_id="uuid"
).info("Tool executed successfully", execution_time_ms=12.5)
```

**Log Levels**:
- ERROR: Tool failures, validation errors
- WARNING: Sandbox violations, confirmation prompts
- INFO: Tool executions (audit-level)
- DEBUG: LLM requests/responses, path resolution

**Acceptance Criteria**:
- All logs parseable as JSON (via `--json-logs` flag)
- Log output respects `--verbose` flag
- No sensitive data (file contents) in logs

## Out of Scope (v0.1.0)

The following features are **explicitly excluded** from MVP:

- ❌ Streaming responses from Ollama
- ❌ Multi-user support / authentication
- ❌ Web UI / HTTP API
- ❌ Conversation persistence (save/load)
- ❌ Tool result caching (LRU cache)
- ❌ Metrics export (Prometheus)
- ❌ Non-filesystem tools (git, docker, database)
- ❌ Cloud deployment (Kubernetes, Docker)

## Traceability Matrix

| Requirement | WBS Tasks | Tests |
|-------------|-----------|-------|
| FR-001 | WBS-003, WBS-004 | test_tools.py |
| FR-002 | WBS-005 | test_orchestrator.py |
| FR-003 | WBS-006 | test_cli.py |
| FR-004 | WBS-007 | test_security.py |
| FR-005 | WBS-008 | test_audit.py |
| FR-006 | WBS-002 | test_ollama_client.py |
| NFR-001 | WBS-009 | test_performance.py |
| NFR-005 | WBS-010 | CI: ruff, basedpyright |
