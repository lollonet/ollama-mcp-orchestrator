# Infrastructure & Operations

## Deployment Model

**Local-First CLI Tool** (no cloud deployment for v0.1.0)

### Installation Methods

#### Method 1: uv tool install (Recommended)

```bash
# Install globally via uv
uv tool install ollama-mcp-orchestrator

# Verify installation
ollama-fs --version
```

**Benefits**:
- Isolated virtual environment
- Single command install
- Automatic dependency resolution

#### Method 2: pipx (Alternative)

```bash
pipx install ollama-mcp-orchestrator
ollama-fs --version
```

#### Method 3: Development Install

```bash
git clone https://github.com/USER/ollama-mcp-orchestrator
cd ollama-mcp-orchestrator
uv venv
uv pip install -e ".[dev]"
```

## System Requirements

### Hardware

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | 2 cores | 8+ cores (for Llama3.3:70b) |
| **RAM** | 8 GB | 64+ GB (Mac Studio M2 Ultra) |
| **Disk** | 10 GB | 50+ GB (for multiple models) |
| **GPU** | None | Metal (macOS) / CUDA (Linux) |

### Software

| Dependency | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.12+ | Runtime |
| **uv** | latest | Package manager |
| **Ollama** | 0.1.0+ | LLM inference |
| **Git** | 2.0+ | Source control |

### Operating Systems

| OS | Status | Notes |
|----|--------|-------|
| **macOS** | ✅ Supported | Primary development platform (Apple Silicon) |
| **Debian Linux** | ✅ Supported | Secondary platform (x86_64) |
| **Ubuntu Linux** | ⚠️ Untested | Should work (similar to Debian) |
| **Windows** | ❌ Unsupported | Path handling differences (v0.2.0) |

## Configuration Management

### Configuration Hierarchy

```
Effective Config = CLI Args > Env Vars > Config File > Defaults
```

### Configuration File

**Location**: `~/.ollama-fs/config.yaml`

**Example**:
```yaml
# Ollama settings
ollama_model: qwen2.5:32b
ollama_host: http://localhost:11434

# Security sandbox
allowed_paths:
  - ~/projects
  - ~/documents
  - ~/Code

# Performance limits
max_iterations: 15
max_context_tokens: 32000
file_size_limit_mb: 10
search_timeout_seconds: 30

# Logging
log_level: INFO
audit:
  enabled: true
  log_path: ~/.ollama-fs/audit.jsonl
  log_reads: false
  rotation_size_mb: 100
```

### Environment Variables

```bash
# Override config file values
export OLLAMA_FS_OLLAMA_MODEL=llama3.3:70b
export OLLAMA_FS_LOG_LEVEL=DEBUG
export OLLAMA_FS_ALLOWED_PATHS="~/projects:~/documents"
```

### Runtime CLI Override

```bash
# Override for single session
ollama-fs chat --model qwen3-coder:30b --verbose
```

## Monitoring & Observability

### Logging

**Log Levels**:
- **DEBUG**: Tool execution details, LLM requests/responses
- **INFO**: Tool completions, agent loop progress
- **WARNING**: Confirmation prompts, sandbox violations
- **ERROR**: Tool failures, validation errors

**Log Formats**:

1. **Human-Readable** (default):
```
2026-01-21 10:30:00 | INFO | Tool: fs_read_file completed in 12.5ms
```

2. **JSON** (--json-logs):
```json
{
  "timestamp": "2026-01-21T10:30:00.123Z",
  "level": "INFO",
  "message": "Tool completed",
  "context": {
    "tool_name": "fs_read_file",
    "execution_time_ms": 12.5,
    "session_id": "uuid"
  }
}
```

### Audit Trail

**Location**: `~/.ollama-fs/audit.jsonl`

**Rotation**: Automatic at 100MB (configurable)

**Retention**: Indefinite (user manages deletion)

**Analysis Example**:
```bash
# Count operations by type
jq -r '.action' ~/.ollama-fs/audit.jsonl | sort | uniq -c

# Find failed operations
jq 'select(.success == false)' ~/.ollama-fs/audit.jsonl

# Operations in last hour
jq "select(.timestamp > \"$(date -u -v-1H '+%Y-%m-%dT%H:%M:%S')\")" audit.jsonl
```

### Metrics (v0.2.0 - Future)

**Prometheus Export** (optional):

```
# HELP ollama_fs_tool_calls_total Total tool calls executed
# TYPE ollama_fs_tool_calls_total counter
ollama_fs_tool_calls_total{tool="fs_read_file",success="true"} 142

# HELP ollama_fs_tool_latency_seconds Tool execution latency
# TYPE ollama_fs_tool_latency_seconds histogram
ollama_fs_tool_latency_seconds_bucket{tool="fs_read_file",le="0.01"} 120
ollama_fs_tool_latency_seconds_bucket{tool="fs_read_file",le="0.05"} 140
ollama_fs_tool_latency_seconds_bucket{tool="fs_read_file",le="+Inf"} 142

# HELP ollama_fs_agent_loop_iterations Agent loop iterations per query
# TYPE ollama_fs_agent_loop_iterations histogram
ollama_fs_agent_loop_iterations_bucket{le="1"} 45
ollama_fs_agent_loop_iterations_bucket{le="3"} 78
ollama_fs_agent_loop_iterations_bucket{le="10"} 95
```

## Error Tracking

### Error Categories

| Category | Example | User Action |
|----------|---------|-------------|
| **User Error** | Invalid path, missing file | Clear error message + suggestion |
| **System Error** | Ollama down, disk full | Retry with backoff |
| **Programming Error** | Unexpected exception | Report to GitHub Issues |

### Error Handling Pattern

```python
try:
    result = await execute_tool(tool_call)
except FileNotFoundError as e:
    # User Error: Clear, actionable message
    return f"❌ File not found: {e.filename}\n💡 Check the path and try again"

except ollama.RequestError as e:
    # System Error: Retry logic
    logger.warning(f"Ollama request failed, retrying... {e}")
    await asyncio.sleep(1)
    result = await execute_tool(tool_call)  # Retry

except Exception as e:
    # Programming Error: Full context for debugging
    logger.exception("Unexpected error in tool execution")
    return f"❌ Internal error: {type(e).__name__}\n💡 Please report this at: <GitHub URL>"
```

## Disaster Recovery

### Data Loss Scenarios

| Scenario | Impact | Recovery |
|----------|--------|----------|
| **Config file deleted** | LOW | Use defaults, recreate from template |
| **Audit log deleted** | MEDIUM | Historic data lost, logging continues |
| **Ollama models deleted** | HIGH | Re-pull models (ollama pull) |

### Backup Recommendations

**Not Automated** (user responsibility):
- Config file: Backup `~/.ollama-fs/` directory
- Audit logs: Periodic copy to archive location
- Ollama models: Re-pullable from registry

## CI/CD Pipeline

### GitHub Actions Workflows

#### 1. **tests.yml** (on push/PR)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [macos-latest, ubuntu-latest]
        python-version: ["3.12", "3.13"]

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Install dependencies
        run: uv pip install -e ".[dev]"

      - name: Run tests
        run: uv run pytest -v --cov=ollama_mcp --cov-report=term-missing

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

#### 2. **security.yml** (on push)

```yaml
name: Security

on: [push]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run gitleaks
        uses: gitleaks/gitleaks-action@v2

      - name: Run Bandit
        run: |
          pip install bandit
          bandit -r src/

      - name: Run Safety
        run: |
          pip install safety
          safety check
```

#### 3. **quality.yml** (on push/PR)

```yaml
name: Code Quality

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Lint with Ruff
        run: |
          uv pip install ruff
          ruff check src/ tests/

      - name: Format check
        run: ruff format --check src/ tests/

      - name: Type check
        run: |
          uv pip install basedpyright
          basedpyright src/ tests/
```

#### 4. **release.yml** (on tag push)

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build package
        run: |
          pip install build
          python -m build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          password: ${{ secrets.PYPI_API_TOKEN }}
```

## Operational Runbooks

### Runbook 1: Fresh Install

```bash
# 1. Install Ollama
brew install ollama  # macOS
# OR: curl -fsSL https://ollama.com/install.sh | sh  # Linux

# 2. Start Ollama service
ollama serve &

# 3. Pull recommended model
ollama pull qwen2.5:32b

# 4. Install orchestrator
uv tool install ollama-mcp-orchestrator

# 5. Create config
mkdir -p ~/.ollama-fs
cat > ~/.ollama-fs/config.yaml <<EOF
allowed_paths:
  - ~/projects
ollama_model: qwen2.5:32b
EOF

# 6. Test installation
ollama-fs ask "List files in ~/projects"
```

### Runbook 2: Troubleshooting Ollama Connection

```bash
# Check if Ollama is running
curl http://localhost:11434/api/version

# If not, start Ollama
ollama serve &

# Verify models available
ollama list

# If model missing, pull it
ollama pull qwen2.5:32b

# Test with orchestrator
ollama-fs --verbose ask "test"
```

### Runbook 3: Audit Log Analysis

```bash
# Find all failed operations
jq 'select(.success == false)' ~/.ollama-fs/audit.jsonl

# Count operations by tool
jq -r '.tool' ~/.ollama-fs/audit.jsonl | sort | uniq -c

# Average execution time by tool
jq -s 'group_by(.tool) | map({tool: .[0].tool, avg_ms: (map(.execution_time_ms) | add / length)})' audit.jsonl

# Security events (access outside sandbox)
jq 'select(.error | contains("SecurityError"))' audit.jsonl
```

## Cost Estimation

**Monthly Cost**: $0 (local deployment)

| Component | Cost |
|-----------|------|
| Ollama (local) | $0 |
| Compute (user's machine) | $0 |
| Storage (models + logs) | $0 (uses existing disk) |
| Network | $0 (no cloud API calls) |

**One-Time Costs**:
- Hardware: User's existing Mac/Linux machine
- Ollama models: Free (open weights)

## Performance Benchmarks (Target)

### Tool Latency (p95)

| Tool | Target (ms) | Notes |
|------|-------------|-------|
| `fs_read_file` (1 KB) | < 10 | SSD read |
| `fs_read_file` (1 MB) | < 50 | Sequential read |
| `fs_write_file` (1 KB) | < 15 | SSD write |
| `fs_list_directory` (100 files) | < 30 | Directory scan |
| `fs_search` (1000 files) | < 500 | Glob pattern match |

### Agent Loop Performance

| Metric | Target |
|--------|--------|
| 1-step query (read only) | < 2s |
| 3-step query (search + read + summarize) | < 5s |
| 5-step query (complex workflow) | < 10s |

**Note**: LLM inference time dominates (500-1000ms per call)
