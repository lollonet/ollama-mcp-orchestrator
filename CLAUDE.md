# Project-Specific AI Instructions

## Project Context

**Ollama-MCP Filesystem Orchestrator** is a production-grade Python CLI tool that enables local Ollama LLMs to safely access the filesystem through the Model Context Protocol (MCP).

## Tech Stack

- **Language**: Python 3.12+ (strict type hints, async/await)
- **Package Manager**: uv (fast, reliable)
- **CLI Framework**: Typer + Rich
- **Validation**: Pydantic v2
- **Logging**: Loguru
- **Testing**: pytest + pytest-asyncio + pytest-cov
- **Linting**: ruff (check + format)
- **Type Checking**: basedpyright (strict mode)

## Coding Conventions

### Python Style

- **Type hints**: REQUIRED on all functions (basedpyright strict mode)
- **Docstrings**: Google style for all public APIs
- **Line length**: 100 characters (ruff enforced)
- **Import order**: Standard lib → Third party → Local (ruff isort)
- **Async**: Use async/await for all I/O operations

### File Structure

```
src/ollama_mcp/
├── __init__.py          # Package exports
├── cli.py               # Typer CLI commands
├── config.py            # Pydantic Settings
├── orchestrator.py      # Agent loop core
├── mcp_server/
│   ├── server.py        # FastMCP server
│   ├── security.py      # Path validation
│   └── tools/
│       └── filesystem.py # 9 filesystem tools
├── ollama_client/
│   ├── client.py        # Ollama wrapper
│   └── prompts.py       # System prompts
└── utils/
    ├── logging.py       # Loguru config
    └── audit.py         # JSONL audit trail
```

### Naming Conventions

- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions**: `snake_case()`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: `_leading_underscore`
- **Type vars**: `T`, `ModelT`, etc.

### Pydantic Models

```python
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings

class ToolCall(BaseModel):
    """Docstring describing the model."""
    name: str = Field(..., description="Tool name")
    arguments: dict[str, Any] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate tool name exists."""
        if v not in VALID_TOOLS:
            raise ValueError(f"Unknown tool: {v}")
        return v
```

## Security Requirements

### Path Validation

- ALL filesystem paths MUST be validated via `security.validate_path()`
- NEVER use `os.system()` or `subprocess` for filesystem operations
- ALWAYS use `Path().resolve()` before accessing files
- BLOCK paths containing `../` or outside `ALLOWED_PATHS`

### Confirmation Prompts

Required for:
- Deleting non-empty directories
- Overwriting files > 1MB
- Operations affecting > 100 files

### Audit Logging

Log to JSONL:
- ALL write operations
- ALL delete operations
- ALL move/copy operations
- OPTIONAL: read operations (if `log_reads=true`)

## Testing Requirements

### Test Structure

```
tests/
├── conftest.py          # Shared fixtures
├── test_models.py       # Pydantic model tests
├── test_security.py     # Path validation tests
├── test_tools_basic.py  # Tools: read, list, write
├── test_tools_extended.py # Tools: delete, move, copy, search
├── test_ollama_client.py # LLM client tests (mocked)
├── test_orchestrator.py # Agent loop tests
├── test_cli.py          # CLI command tests
└── test_integration.py  # End-to-end scenarios
```

### Test Markers

```python
@pytest.mark.unit
def test_path_validation():
    ...

@pytest.mark.integration
async def test_agent_loop_3_step():
    ...

@pytest.mark.security
def test_path_traversal_blocked():
    ...
```

### Coverage Requirements

- **Line coverage**: > 80%
- **Branch coverage**: > 70%
- **Critical paths**: 100% (security, agent loop)

## Quality Gates

### Pre-commit (Local)

```bash
ruff check src/ tests/
ruff format src/ tests/
basedpyright src/ tests/
pytest -v --cov=ollama_mcp
```

### CI (GitHub Actions)

- Linting (ruff check)
- Formatting (ruff format --check)
- Type checking (basedpyright)
- Tests (pytest with coverage)
- Security scan (bandit, safety, gitleaks)

### BassCodeBase Integration

```bash
bass check          # Quick gates (lint, format, typecheck)
bass check --all    # Full gates (+ complexity, coverage, traceability)
```

## Error Handling

### Error Categories

```python
# User errors: Clear, actionable messages
raise FileNotFoundError(f"File not found: {path}\n💡 Check the path and try again")

# System errors: Retry with backoff
@retry(stop=stop_after_attempt(3), wait=wait_exponential())
async def call_ollama():
    ...

# Programming errors: Full context for debugging
logger.exception("Unexpected error in tool execution")
raise RuntimeError(f"Internal error: {type(e).__name__}")
```

## Agent Loop Pattern

### ReAct Implementation

```python
while not state.completed and iteration < max_iterations:
    # 1. PLANNING: LLM decides next action
    response = await ollama_client.chat(state.messages)

    # 2. TOOL_CALL: Parse JSON if tool requested
    tool_call = parse_tool_call(response)
    if not tool_call:
        state.completed = True
        return response  # Final answer

    # 3. EXECUTION: Run MCP tool with timeout
    tool_result = await execute_tool(tool_call)

    # 4. OBSERVATION: Add result to context
    state.messages.append(format_observation(tool_result))

    # 5. REFLECTION: Loop continues automatically

    iteration += 1
```

## Traceability

### Requirement Tags

All commits MUST reference a requirement:

```bash
git commit -m "feat: add fs_search tool (REQ-001)"
git commit -m "fix: path traversal vulnerability (REQ-004)"
git commit -m "docs: update architecture (ARC-001)"
```

### WBS Tracking

Each implementation maps to WBS tasks:
- REQ-001 → WBS-004, WBS-005
- REQ-002 → WBS-007
- REQ-003 → WBS-008
- REQ-004 → WBS-003, WBS-010

## Performance Targets

- **Tool execution**: < 100ms (p95) for files < 1MB
- **Agent loop**: < 5s total for 3-step queries
- **LLM inference**: ~500-1000ms per call (Qwen2.5:32b)

## Documentation Standards

### Docstring Format

```python
async def validate_path(path: str, allowed_paths: list[Path]) -> Path:
    """Validate path is within allowed sandbox.

    Args:
        path: File path to validate (relative or absolute)
        allowed_paths: List of allowed base directories

    Returns:
        Resolved absolute path if valid

    Raises:
        InvalidPathError: Path is malformed
        SecurityError: Path outside allowed sandbox

    Example:
        >>> path = await validate_path("~/projects/test.py", [Path.home() / "projects"])
        >>> print(path)
        /Users/claudio/projects/test.py
    """
```

### README Updates

When adding features:
1. Update README.md "Features" section
2. Add example to "Example Session" if user-visible
3. Update CHANGELOG.md with entry
4. Update relevant REQ-### document

## Dependencies

### Adding New Dependencies

1. Add to `pyproject.toml` dependencies
2. Document rationale in TECH-001.runtime.md
3. Check license compatibility (MIT preferred)
4. Test on Mac + Linux platforms

### Security Auditing

```bash
# Before committing new dependencies
uv run safety check
uv run bandit -r src/
```

## Release Process

### Version Bumping

```bash
# Update version in:
- pyproject.toml
- src/ollama_mcp/__init__.py
- CHANGELOG.md (move from Unreleased)

# Tag and push
git tag v0.1.0
git push origin v0.1.0
```

### Publishing to PyPI

```bash
# Build
python -m build

# Test upload
twine upload --repository testpypi dist/*

# Production upload
twine upload dist/*
```

## Non-Negotiables

1. ❌ NEVER skip type hints
2. ❌ NEVER ignore security validation
3. ❌ NEVER commit secrets or API keys
4. ❌ NEVER merge without passing CI
5. ✅ ALWAYS test security-critical code
6. ✅ ALWAYS document public APIs
7. ✅ ALWAYS reference REQ-### in commits
8. ✅ ALWAYS use async/await for I/O
