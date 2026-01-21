# Ollama-MCP Filesystem Orchestrator

Python orchestrator that lets local Ollama models safely access the filesystem through the Model Context Protocol (MCP). Features an autonomous agent loop with planning/execution/reflection, security sandbox, and audit logging.

<!-- Badges (will be enabled after first release)
[![Tests](https://github.com/lollonet/ollama-mcp-orchestrator/actions/workflows/tests.yml/badge.svg)](https://github.com/lollonet/ollama-mcp-orchestrator/actions/workflows/tests.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
-->

## What it does

- **Agent loop**: Automatically plans, executes, and reflects on filesystem tasks (ReAct pattern)
- **Security sandbox**: All paths validated against allowed directories, prevents traversal attacks
- **9 filesystem tools**: read, write, list, create_dir, delete, move, copy, search, file_info
- **Audit logging**: JSONL trail of all filesystem modifications
- **Type-safe**: Pydantic v2 models, basedpyright strict mode
- **Tested**: Comprehensive security and integration tests

## Quick Start

### Prerequisites

```bash
# 1. Install Ollama
brew install ollama  # macOS
# OR: curl -fsSL https://ollama.com/install.sh | sh  # Linux

# 2. Start Ollama and pull model
ollama serve &
ollama pull qwen2.5:32b
```

### Installation

```bash
# Install globally via uv (recommended)
uv tool install ollama-mcp-orchestrator

# Verify installation
ollama-fs --version
```

### First Run

```bash
# Interactive chat mode
ollama-fs chat

# Single query mode
ollama-fs ask "List all Python files in ~/projects"

# With custom settings
ollama-fs chat --model llama3.3:70b --verbose
```

### Example Session

```
$ ollama-fs chat

┌────────────────────────────────────────────────┐
│  🤖 Ollama MCP Orchestrator v0.1.0              │
│  📁 Allowed: ~/projects                        │
│  🔧 Model: qwen2.5:32b                         │
└────────────────────────────────────────────────┘

You: List Python files in ~/projects/myapp, find the largest, and summarize its imports

[Tool] fs_search(pattern="*.py", path="~/projects/myapp")
✓ Found 8 Python files in 15.3ms

[Tool] fs_file_info(path="~/projects/myapp/main.py")
✓ main.py: 4.5 KB (largest) in 8.2ms

[Tool] fs_read_file(path="~/projects/myapp/main.py")
✓ Read 4.5 KB in 12.1ms

A: Found 8 Python files in ~/projects/myapp. The largest is **main.py** (4.5 KB).

**Imports summary**:
- fastapi: Web framework
- pydantic: Data validation
- ollama: LLM client
- loguru: Structured logging

Total execution time: 2.3s (3 iterations)

You: /exit
```

## Architecture

```
┌─────────────────────────────────────────┐
│           CLI Layer                      │
│  - Typer commands                       │
│  - Rich formatting                      │
└─────────────────────────────────────────┘
              ▼
┌─────────────────────────────────────────┐
│        Orchestrator Core                │
│  - Agent loop (ReAct)                   │
│  - Tool registry                        │
│  - Conversation management              │
└─────────────────────────────────────────┘
         ▼                  ▼
┌──────────────────┐  ┌──────────────────┐
│  Ollama Client   │  │   MCP Server     │
│  - LLM calls     │  │  - 9 FS tools    │
│  - Retry logic   │  │  - Security      │
└──────────────────┘  └──────────────────┘
```

## Security Sandbox

All filesystem operations are restricted to allowed paths:

```yaml
# ~/.ollama-fs/config.yaml
allowed_paths:
  - ~/projects
  - ~/documents
```

**Security features**:
- Path traversal prevention (blocks `../`, absolute paths outside sandbox)
- Symlink resolution and validation
- Confirmation prompts for destructive operations
- JSONL audit log for all modifications

## Configuration

### Config File

```yaml
# ~/.ollama-fs/config.yaml
ollama_model: qwen2.5:32b
ollama_host: http://localhost:11434

allowed_paths:
  - ~/projects
  - ~/Code

max_iterations: 15
max_context_tokens: 32000
file_size_limit_mb: 10

log_level: INFO
audit:
  log_path: ~/.ollama-fs/audit.jsonl
  log_reads: false
```

### Environment Variables

```bash
export OLLAMA_FS_OLLAMA_MODEL=llama3.3:70b
export OLLAMA_FS_LOG_LEVEL=DEBUG
export OLLAMA_FS_ALLOWED_PATHS="~/projects:~/documents"
```

### CLI Flags

```bash
ollama-fs chat --model qwen3-coder:30b --verbose --allowed-paths ~/projects
```

**Precedence**: CLI flags > Env vars > Config file > Defaults

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/USER/ollama-mcp-orchestrator
cd ollama-mcp-orchestrator

# Install with dev dependencies
uv venv
uv pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Quality Gates

```bash
# Lint + format
ruff check src/ tests/
ruff format src/ tests/

# Type check
basedpyright src/ tests/

# Tests with coverage
pytest -v --cov=ollama_mcp --cov-report=term-missing

# All checks (mimics CI)
ruff check . && ruff format --check . && basedpyright . && pytest
```

### Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest -m unit

# Integration tests
pytest -m integration

# Security tests
pytest -m security

# With coverage
pytest --cov=ollama_mcp --cov-report=html
```

## BassCodeBase Integration

This project is configured for [BassCodeBase](https://github.com/lollonet/BassCodeBase) quality standards.

```bash
# Install BassCodeBase
uv tool install basscodebase

# Adopt standards (detects .bass-ready file)
bass adopt

# Run quality gates
bass check

# Run all gates (includes complexity, coverage)
bass check --all
```

## Documentation

- [00-VISION.md](docs/00-VISION.md) - Project vision and success metrics
- [01-REQUIREMENTS.md](docs/01-REQUIREMENTS.md) - Functional requirements
- [02-ARCHITECTURE.md](docs/02-ARCHITECTURE.md) - System architecture
- [03-API-CONTRACTS.md](docs/03-API-CONTRACTS.md) - Tool API specifications
- [04-DATA-MODELS.md](docs/04-DATA-MODELS.md) - Pydantic models
- [05-UI-UX.md](docs/05-UI-UX.md) - CLI interface design
- [06-SECURITY.md](docs/06-SECURITY.md) - Security architecture
- [07-INFRASTRUCTURE.md](docs/07-INFRASTRUCTURE.md) - Deployment guide
- [08-WBS.md](docs/08-WBS.md) - Work breakdown structure

### BassCodeBase Documentation

- [docs/requirements/REQ-INDEX.md](docs/requirements/REQ-INDEX.md) - Requirements index
- [docs/architecture/ARC-001.context.md](docs/architecture/ARC-001.context.md) - Architecture decisions
- [docs/technology/TECH-001.runtime.md](docs/technology/TECH-001.runtime.md) - Technology stack
- [CONTROL.yaml](CONTROL.yaml) - Quality gate configuration

## Roadmap

### v0.1.0 (MVP) - Current
- [x] 9 filesystem tools (read, write, list, create_dir, delete, move, copy, search, file_info)
- [x] Agent loop with ReAct pattern
- [x] Security sandbox with path validation
- [x] CLI interface (chat + ask modes)
- [x] Audit logging (JSONL)
- [ ] Tests (target: > 80% coverage)
- [ ] Documentation complete

### v0.2.0 (Planned)
- [ ] Streaming LLM responses
- [ ] LRU cache for idempotent tools
- [ ] Multi-conversation support
- [ ] Prometheus metrics export
- [ ] Windows platform support

### v0.3.0 (Future)
- [ ] Web UI
- [ ] Remote MCP servers
- [ ] Custom tool plugins
- [ ] Advanced git operations

## Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

### Development Process

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes with tests
3. Ensure quality gates pass: `bash check-all.sh`
4. Commit with REQ tag: `git commit -m "feat: add streaming (REQ-014)"`
5. Push and open PR

## License

MIT © 2026 Claudio

---

**Status**: In Development (v0.1.0)

Report issues: https://github.com/lollonet/ollama-mcp-orchestrator/issues
