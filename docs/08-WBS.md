# Work Breakdown Structure

> **Documento storico (gennaio 2026), superato il 2026-08-16.** Il progetto
> non viene implementato: vedi [ARC-002](architecture/ARC-002.closure-decision.md)
> e lo [spike sui guardrail MCP](09-SPIKE-MCP-GUARDRAILS.md).


## Project Phases

The implementation follows **5 incremental phases** as specified:

1. **Phase 1**: MCP server with base tools (read, list, write)
2. **Phase 2**: Orchestrator with agent loop
3. **Phase 3**: CLI and logging
4. **Phase 4**: Advanced security and testing
5. **Phase 5**: Optimizations and nice-to-have features

---

## Phase 1: MCP Server Foundation

### WBS-001: Project Setup

**Priority**: P0 (Critical)
**Effort**: S (Small)
**Dependencies**: None
**Phase**: Setup

#### Description

Initialize project structure, configure development environment, set up quality gates.

#### Acceptance Criteria

- [ ] `pyproject.toml` configured with dependencies
- [ ] `src/ollama_mcp/` directory structure created
- [ ] `tests/` directory with `conftest.py`
- [ ] `ruff`, `basedpyright`, `pytest` configured
- [ ] Pre-commit hooks installed
- [ ] GitHub repository created with CI workflows

#### Technical Notes

```bash
# Initialize with uv
uv init ollama-mcp-orchestrator
cd ollama-mcp-orchestrator
uv add pydantic typer rich ollama mcp loguru httpx aiofiles tenacity
uv add --dev pytest pytest-asyncio pytest-cov ruff basedpyright
```

#### Files

- `pyproject.toml`
- `README.md`
- `.gitignore`
- `.github/workflows/tests.yml`

---

### WBS-002: Pydantic Models

**Priority**: P0
**Effort**: M
**Dependencies**: WBS-001
**Phase**: Setup

#### Description

Implement all Pydantic data models: Config, ToolCall, ToolResult, AgentState, FileInfo, etc.

#### Acceptance Criteria

- [ ] `OrchestratorConfig` with Settings integration
- [ ] `ToolCall`, `ToolResult`, `Message` models
- [ ] `AgentState` with state management methods
- [ ] `FileInfo`, `DirectoryListing`, `SearchResult` models
- [ ] `AuditLogEntry` with JSONL serialization
- [ ] All models have type hints + validation
- [ ] Unit tests for model validation

#### Files

- `src/ollama_mcp/config.py`
- `src/ollama_mcp/mcp_server/models.py`
- `tests/test_models.py`

---

### WBS-003: Security Module

**Priority**: P0
**Effort**: M
**Dependencies**: WBS-002
**Phase**: Core

#### Description

Implement path validation and sandbox enforcement.

#### Acceptance Criteria

- [ ] `validate_path()` function with comprehensive checks
- [ ] Path traversal prevention (../../)
- [ ] Symlink resolution and validation
- [ ] ALLOWED_PATHS sandbox enforcement
- [ ] Security tests with adversarial inputs
- [ ] Clear error messages for violations

#### Technical Notes

```python
# Test cases must include:
- ../../etc/passwd
- /etc/passwd
- ~/../../etc/passwd
- symlinks outside sandbox
```

#### Files

- `src/ollama_mcp/mcp_server/security.py`
- `tests/test_security.py`

---

### WBS-004: Filesystem Tools (Base)

**Priority**: P0
**Effort**: L
**Dependencies**: WBS-003
**Phase**: Core

#### Description

Implement 3 core filesystem tools using FastMCP:
1. `fs_read_file`
2. `fs_list_directory`
3. `fs_write_file`

#### Acceptance Criteria

- [ ] FastMCP server initialized
- [ ] `fs_read_file` with size limit enforcement
- [ ] `fs_list_directory` with recursive option
- [ ] `fs_write_file` with parent directory creation
- [ ] All tools use `validate_path()` before execution
- [ ] Tool execution timing measured
- [ ] Comprehensive unit tests

#### Files

- `src/ollama_mcp/mcp_server/server.py`
- `src/ollama_mcp/mcp_server/tools/filesystem.py`
- `tests/test_tools_basic.py`

---

### WBS-005: Filesystem Tools (Extended)

**Priority**: P1
**Effort**: M
**Dependencies**: WBS-004
**Phase**: Core

#### Description

Implement remaining 6 filesystem tools:
4. `fs_create_directory`
5. `fs_delete`
6. `fs_move`
7. `fs_copy`
8. `fs_search`
9. `fs_file_info`

#### Acceptance Criteria

- [ ] All 6 tools implemented with MCP annotations
- [ ] Confirmation prompts for destructive operations
- [ ] Search with glob + content matching
- [ ] File metadata extraction
- [ ] Integration tests for complex scenarios
- [ ] Error handling for edge cases

#### Files

- `src/ollama_mcp/mcp_server/tools/filesystem.py` (extended)
- `tests/test_tools_extended.py`

---

## Phase 2: Orchestrator & Agent Loop

### WBS-006: Ollama Client Wrapper

**Priority**: P0
**Effort**: M
**Dependencies**: WBS-002
**Phase**: Core

#### Description

Implement Ollama client wrapper with retry logic and model verification.

#### Acceptance Criteria

- [ ] OllamaClient class with async/await
- [ ] Model availability check on init
- [ ] Retry logic with exponential backoff (tenacity)
- [ ] System prompt injection
- [ ] Error handling for connection failures
- [ ] Mock tests for offline testing

#### Technical Notes

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
async def chat(messages: list[dict]) -> str:
    ...
```

#### Files

- `src/ollama_mcp/ollama_client/client.py`
- `src/ollama_mcp/ollama_client/prompts.py`
- `tests/test_ollama_client.py`

---

### WBS-007: Orchestrator Core

**Priority**: P0
**Effort**: XL
**Dependencies**: WBS-006, WBS-004
**Phase**: Core

#### Description

Implement agent loop with ReAct pattern (plan → execute → observe → reflect).

#### Acceptance Criteria

- [ ] `Orchestrator` class with configurable max_iterations
- [ ] Agent loop implements 8 stages (USER_INPUT → RESPONSE)
- [ ] Tool call parsing from LLM JSON responses
- [ ] Tool execution with timeout handling
- [ ] Context management (add messages to history)
- [ ] Loop termination conditions (completed or max_iterations)
- [ ] Integration test: 3-step task (search → read → summarize)

#### Algorithm

```
while not completed and iteration < max_iterations:
    1. LLM plans next action
    2. Parse tool call (if any)
    3. Execute tool via MCP
    4. Add result to context
    5. LLM reflects on progress
    6. Check if task completed
```

#### Files

- `src/ollama_mcp/orchestrator.py`
- `tests/test_orchestrator.py`

---

## Phase 3: CLI & Logging

### WBS-008: CLI Interface

**Priority**: P0
**Effort**: L
**Dependencies**: WBS-007
**Phase**: Enhancement

#### Description

Implement Typer CLI with chat and ask commands.

#### Acceptance Criteria

- [ ] `ollama-fs chat` - Interactive REPL
- [ ] `ollama-fs ask "query"` - Single query mode
- [ ] `--model`, `--verbose`, `--allowed-paths` flags
- [ ] Rich console formatting (banners, tables, progress)
- [ ] `config show` and `config set` commands
- [ ] Interactive prompts for confirmations
- [ ] REPL commands (/help, /history, /exit)

#### Files

- `src/ollama_mcp/cli.py`
- `tests/test_cli.py`

---

### WBS-009: Logging & Audit

**Priority**: P1
**Effort**: M
**Dependencies**: WBS-008
**Phase**: Enhancement

#### Description

Implement structured logging (Loguru) and audit trail (JSONL).

#### Acceptance Criteria

- [ ] Loguru configured with context binding
- [ ] Log levels: DEBUG, INFO, WARNING, ERROR
- [ ] JSON log output option (--json-logs)
- [ ] Audit log writer (JSONL format)
- [ ] Audit log rotation at 100MB
- [ ] Selective logging (log_reads config option)
- [ ] Log analysis examples in docs

#### Technical Notes

```python
logger.bind(
    tool_name="fs_write_file",
    path="/path/to/file",
    session_id=state.session_id
).info("Tool executed", execution_time_ms=12.5)
```

#### Files

- `src/ollama_mcp/utils/logging.py`
- `src/ollama_mcp/utils/audit.py`
- `tests/test_audit.py`

---

## Phase 4: Security & Testing

### WBS-010: Security Hardening

**Priority**: P0
**Effort**: M
**Dependencies**: WBS-003
**Phase**: Enhancement

#### Description

Add advanced security features and comprehensive security tests.

#### Acceptance Criteria

- [ ] macOS system path blocking (/System, /Library, etc.)
- [ ] Symlink exploitation prevention
- [ ] Confirmation prompts implemented
- [ ] Security audit recommendations documented
- [ ] Penetration testing checklist
- [ ] Security tests with 20+ adversarial inputs

#### Files

- `src/ollama_mcp/mcp_server/security.py` (extended)
- `tests/test_security_advanced.py`
- `docs/SECURITY.md`

---

### WBS-011: Comprehensive Testing

**Priority**: P0
**Effort**: L
**Dependencies**: All previous
**Phase**: Enhancement

#### Description

Achieve > 80% test coverage with unit, integration, and security tests.

#### Acceptance Criteria

- [ ] Unit tests for all modules
- [ ] Integration tests for agent loop
- [ ] Security tests for path validation
- [ ] Performance benchmarks for tools
- [ ] Mock tests for offline scenarios
- [ ] Coverage report > 80% line, > 70% branch
- [ ] CI runs all tests on Mac + Linux

#### Files

- `tests/conftest.py` (fixtures)
- `tests/test_performance.py`
- `tests/test_integration.py`

---

## Phase 5: Optimizations & Nice-to-Have

### WBS-012: Documentation

**Priority**: P1
**Effort**: M
**Dependencies**: WBS-011
**Phase**: Polish

#### Description

Complete README, API docs, examples, and troubleshooting guides.

#### Acceptance Criteria

- [ ] README with quickstart (< 5 min to first run)
- [ ] API reference (auto-generated from docstrings)
- [ ] 5+ example scenarios
- [ ] Security configuration guide
- [ ] Troubleshooting runbook
- [ ] Contributing guide
- [ ] Changelog (Keep a Changelog format)

#### Files

- `README.md`
- `docs/examples/`
- `CONTRIBUTING.md`
- `CHANGELOG.md`

---

### WBS-013: Performance Optimization

**Priority**: P2
**Effort**: M
**Dependencies**: WBS-011
**Phase**: Optimization

#### Description

Optimize tool execution for low latency.

#### Acceptance Criteria

- [ ] Async I/O for all file operations (aiofiles)
- [ ] Lazy imports for faster startup
- [ ] Benchmark suite for regression detection
- [ ] Tool latency < 100ms (p95) verified
- [ ] Agent loop completes 3-step tasks in < 5s

#### Files

- `src/ollama_mcp/mcp_server/tools/filesystem.py` (optimized)
- `benchmarks/tool_latency.py`

---

### WBS-014: Streaming Responses (Optional)

**Priority**: P3 (Nice-to-have)
**Effort**: M
**Dependencies**: WBS-007
**Phase**: Future

#### Description

Stream LLM responses for better UX (v0.2.0 feature).

#### Acceptance Criteria

- [ ] Ollama streaming API integration
- [ ] Rich live display for streaming text
- [ ] Incremental tool call detection
- [ ] Graceful fallback to non-streaming

#### Files

- `src/ollama_mcp/ollama_client/client.py` (streaming)
- `src/ollama_mcp/cli.py` (rich live display)

---

### WBS-015: LRU Cache for Tools (Optional)

**Priority**: P3
**Effort**: S
**Dependencies**: WBS-004
**Phase**: Future

#### Description

Add LRU cache for idempotent read-only tools (v0.2.0).

#### Acceptance Criteria

- [ ] `functools.lru_cache` wrapper for read tools
- [ ] TTL-based cache invalidation
- [ ] Cache hit/miss metrics
- [ ] Configurable cache size

#### Files

- `src/ollama_mcp/utils/cache.py`

---

## Task Dependencies Graph

```
WBS-001 (Setup)
   │
   ├─> WBS-002 (Models)
   │      │
   │      ├─> WBS-003 (Security)
   │      │      │
   │      │      └─> WBS-004 (Tools Base)
   │      │             │
   │      │             ├─> WBS-005 (Tools Extended)
   │      │             │
   │      │             └─> WBS-007 (Orchestrator)
   │      │                    │
   │      │                    └─> WBS-008 (CLI)
   │      │                           │
   │      │                           └─> WBS-009 (Logging)
   │      │
   │      └─> WBS-006 (Ollama Client)
   │             │
   │             └─> WBS-007 (Orchestrator)
   │
   ├─> WBS-010 (Security Hardening)
   │
   └─> WBS-011 (Testing)
          │
          ├─> WBS-012 (Documentation)
          │
          ├─> WBS-013 (Performance)
          │
          ├─> WBS-014 (Streaming) [OPTIONAL]
          │
          └─> WBS-015 (Cache) [OPTIONAL]
```

## Milestones

| Milestone | Tasks | Target | Deliverable |
|-----------|-------|--------|-------------|
| **M1: Foundation** | WBS-001 to WBS-003 | Week 1 | Project setup + security |
| **M2: Core Tools** | WBS-004 to WBS-005 | Week 1-2 | 9 filesystem tools working |
| **M3: Agent Loop** | WBS-006 to WBS-007 | Week 2 | Orchestrator completes 3-step tasks |
| **M4: CLI Ready** | WBS-008 to WBS-009 | Week 2-3 | Usable CLI with logging |
| **M5: Production** | WBS-010 to WBS-011 | Week 3 | Security hardened, tested |
| **M6: Release** | WBS-012 | Week 3 | v0.1.0 released to PyPI |

## Resource Allocation

**Team**: Solo developer (Claudio)
**Estimated Effort**: 80-100 hours total

| Phase | Hours | % of Total |
|-------|-------|------------|
| Phase 1: MCP Server | 20h | 25% |
| Phase 2: Orchestrator | 25h | 31% |
| Phase 3: CLI & Logging | 15h | 19% |
| Phase 4: Security & Tests | 15h | 19% |
| Phase 5: Docs & Polish | 5h | 6% |

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Ollama API changes | LOW | HIGH | Pin to specific version, integration tests |
| Path validation bypass | LOW | HIGH | Comprehensive security tests |
| Performance bottleneck | MEDIUM | MEDIUM | Early benchmarking, profiling |
| Model hallucination | MEDIUM | LOW | Strict JSON parsing, retry logic |
| User adoption | MEDIUM | MEDIUM | Clear docs, working examples |

## Definition of Done

A task is **complete** when:

1. ✅ Code implemented and self-reviewed
2. ✅ Unit tests pass (coverage > 80%)
3. ✅ Docstrings added (Google style)
4. ✅ Type hints added (basedpyright passes)
5. ✅ Ruff linting passes
6. ✅ Integration tests pass (if applicable)
7. ✅ Security tests pass (if applicable)
8. ✅ CI passes on Mac + Linux
9. ✅ Documentation updated
10. ✅ Committed to main branch (via PR if multi-person)
