---
id: TECH-001
title: Runtime Environment & Dependency Management
status: superseded
date: 2026-01-21
authors: [Claudio]
---

# TECH-001: Runtime Environment & Dependency Management

> **Superato il 2026-08-16** — vedi [ARC-002](../architecture/ARC-002.closure-decision.md).

## Context

The Ollama-MCP Filesystem Orchestrator requires a Python runtime with specific dependencies for MCP protocol support, LLM integration, CLI interface, and filesystem operations.

## Problem Statement

**How do we manage Python dependencies and ensure reproducible installations across macOS (Apple Silicon) and Debian Linux?**

## Technology Stack

### Core Runtime

| Component | Version | Rationale |
|-----------|---------|-----------|
| **Python** | 3.12+ | Modern type hints (PEP 695), async/await improvements |
| **uv** | latest | Fastest package manager, replaces pip/poetry/pipenv |
| **Virtual Env** | uv-managed | Isolated dependencies, no global pollution |

### Why Python 3.12+?

- **Type Parameter Syntax (PEP 695)**: Cleaner generics
- **Improved Error Messages**: Better debugging
- **Performance**: 5-10% faster than 3.11
- **asyncio Improvements**: Better async/await performance

### Why uv over pip/poetry?

| Feature | pip | poetry | uv |
|---------|-----|--------|-----|
| **Speed** | Slow | Medium | **10-100x faster** |
| **Lock Files** | ❌ No | ✅ Yes | ✅ Yes |
| **Virtual Envs** | Manual | Built-in | **Built-in + cached** |
| **Dependency Resolution** | Basic | Good | **Excellent** |
| **Cross-platform** | ✅ Yes | ✅ Yes | ✅ Yes |

**Decision**: **uv** for speed and reliability.

## Core Dependencies

### Production Dependencies

```toml
[project]
dependencies = [
    "pydantic>=2.0",           # Data validation, settings
    "typer>=0.9",              # CLI framework
    "rich>=13.0",              # Terminal formatting
    "ollama>=0.1.0",           # Ollama Python client
    "mcp>=0.1.0",              # MCP SDK
    "loguru>=0.7",             # Structured logging
    "httpx>=0.25",             # Async HTTP (for future features)
    "aiofiles>=23.0",          # Async file I/O
    "tenacity>=8.0",           # Retry logic
]
```

### Development Dependencies

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0",             # Testing framework
    "pytest-asyncio>=0.21",    # Async test support
    "pytest-cov>=4.0",         # Coverage reporting
    "ruff>=0.1.0",             # Linting + formatting
    "basedpyright>=1.0",       # Type checking
    "pre-commit>=3.0",         # Git hooks
]
```

## Dependency Rationale

### Why Pydantic v2?

- **30-50x faster** than v1 (Rust core)
- Settings management with env var support
- Excellent validation error messages
- Frozen models for immutable config

### Why Typer over Click/argparse?

- **Type-safe**: Uses Python type hints
- Auto-generated help text
- Rich integration (colors, tables)
- Less boilerplate than Click

### Why Loguru over logging?

- Simpler API (no handlers/formatters)
- Context binding (`logger.bind(session_id=...)`)
- Structured logging (JSON output)
- Async-safe

### Why tenacity over custom retry?

- Declarative retry logic
- Exponential backoff built-in
- Jitter support
- Well-tested library

## Platform Support

### Supported Platforms

| OS | Architecture | Status | Notes |
|----|--------------|--------|-------|
| **macOS** | Apple Silicon (M1/M2/M3) | ✅ Tier 1 | Primary development platform |
| **macOS** | Intel x86_64 | ✅ Tier 2 | Should work, untested |
| **Linux** | Debian 12 x86_64 | ✅ Tier 1 | Secondary platform |
| **Linux** | Ubuntu 22.04+ | ⚠️ Tier 2 | Should work (similar to Debian) |
| **Windows** | Any | ❌ Unsupported | Path handling differences (v0.2.0) |

### Platform-Specific Considerations

#### macOS

```python
# System path protection (macOS-specific)
BLOCKED_MACOS_PATHS = [
    Path("/System"),
    Path("/Library"),
    Path("/usr"),
    Path("/private"),
]
```

#### Linux

```python
# System path protection (Linux-specific)
BLOCKED_LINUX_PATHS = [
    Path("/etc"),
    Path("/usr"),
    Path("/var"),
    Path("/sys"),
    Path("/proc"),
]
```

## Installation Methods

### Method 1: uv tool install (Recommended)

```bash
# Install globally via uv
uv tool install ollama-mcp-orchestrator

# Verify
ollama-fs --version
```

**Pros**:
- Isolated virtual environment
- Single command
- Works from any directory

### Method 2: Development Install

```bash
git clone https://github.com/USER/ollama-mcp-orchestrator
cd ollama-mcp-orchestrator
uv venv
uv pip install -e ".[dev]"
```

**Pros**:
- Editable install
- Access to dev dependencies

## Dependency Locking

### Lock Files

```bash
# Generate lock file
uv pip compile pyproject.toml -o requirements.txt

# Install from lock
uv pip install -r requirements.txt
```

**Benefits**:
- Reproducible builds
- CI/CD consistency
- Security auditing

## Runtime Configuration

### Environment Variables

```bash
# Required
OLLAMA_HOST=http://localhost:11434  # Ollama server URL

# Optional
OLLAMA_FS_LOG_LEVEL=INFO           # Logging level
OLLAMA_FS_AUDIT_LOG=~/.ollama-fs/audit.jsonl
OLLAMA_FS_CONFIG=~/.ollama-fs/config.yaml
```

### System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **Python** | 3.12 | 3.13+ |
| **RAM** | 8 GB | 64 GB (for Llama3.3:70b) |
| **Disk** | 10 GB | 50 GB (for multiple models) |
| **Ollama** | 0.1.0+ | latest |

## Quality Gates

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: ruff-check
        name: Ruff linting
        entry: ruff check --fix
        language: system
        types: [python]

      - id: ruff-format
        name: Ruff formatting
        entry: ruff format
        language: system
        types: [python]

      - id: basedpyright
        name: Type checking
        entry: basedpyright
        language: system
        types: [python]
```

### CI Checks

```yaml
# .github/workflows/quality.yml
- name: Lint
  run: ruff check src/ tests/

- name: Format
  run: ruff format --check src/ tests/

- name: Type check
  run: basedpyright src/ tests/

- name: Tests
  run: pytest -v --cov=ollama_mcp
```

## Dependency Updates

### Strategy

- **Security Updates**: Immediate
- **Minor Updates**: Weekly
- **Major Updates**: Review breaking changes first

### Tools

```bash
# Check for outdated dependencies
uv pip list --outdated

# Update all (test first!)
uv pip install --upgrade -e ".[dev]"
```

## Related Decisions

- **ARC-001**: System architecture (monolith decision)
- **REQ-009**: Configuration management (env vars + config file)

## Consequences

### Positive

- ✅ Fast installations (uv speed)
- ✅ Reproducible builds (lock files)
- ✅ Modern Python features (3.12+)
- ✅ Type safety (Pydantic, basedpyright)

### Negative

- ❌ Python 3.12+ requirement (newer than some systems)
- ❌ uv not as widely adopted as pip/poetry yet
- ❌ No Windows support (v0.1.0)

### Mitigations

- **Python 3.12**: Most modern systems have it, easy to install via `pyenv`
- **uv adoption**: Growing rapidly, official Astral project
- **Windows**: Future feature (v0.2.0)

## Review Notes

- To be reviewed by: Claudio
- Review status: Draft
- Next review: After dependency finalization
