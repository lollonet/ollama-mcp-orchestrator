# Technical Architecture

> **Documento storico (gennaio 2026), superato il 2026-08-16.** Il progetto
> non viene implementato: vedi [ARC-002](architecture/ARC-002.closure-decision.md)
> e lo [spike sui guardrail MCP](09-SPIKE-MCP-GUARDRAILS.md).


## System Design

### Architecture Style

**Monolithic Python Application** (single process, modular design)

**Rationale**:
- Single-user local tool (no scalability needs)
- Simpler deployment (uv install)
- Easier debugging
- Lower latency (no network hops)

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLI Interface                             │
│                    (typer + rich console)                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Orchestrator Core                            │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐     │
│  │ToolRegistry │  │ AgentLoop    │  │ ConversationManager │     │
│  │             │  │              │  │                     │     │
│  │ - register  │  │ - plan       │  │ - history           │     │
│  │ - discover  │  │ - execute    │  │ - context window    │     │
│  │ - validate  │  │ - reflect    │  │ - persistence       │     │
│  └─────────────┘  └──────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌──────────────────────┐         ┌──────────────────────┐
│    Ollama Client     │         │   MCP Client/Server  │
│                      │         │                      │
│ - chat()             │         │ - filesystem tools   │
│ - function calling   │         │ - security sandbox   │
│ - streaming          │         │ - audit logging      │
└──────────────────────┘         └──────────────────────┘
```

## Component Specifications

### CLI Interface (`cli.py`)

**Technology**: Typer + Rich

**Responsibilities**:
- Parse command-line arguments
- Display formatted output (tables, progress bars)
- Handle interactive prompts
- Manage REPL loop for chat mode

**Commands**:
```python
@app.command()
def chat(
    model: str = "qwen2.5:32b",
    verbose: bool = False,
    allowed_paths: list[Path] | None = None
) -> None:
    """Start interactive chat session."""

@app.command()
def ask(
    query: str,
    model: str = "qwen2.5:32b",
    output_format: Literal["text", "json"] = "text"
) -> None:
    """Execute single query and exit."""

@app.command()
def config(action: Literal["show", "set"]) -> None:
    """Manage configuration."""
```

**Data Flow**:
1. User input → Command parser
2. Validate arguments → Create `OrchestratorConfig`
3. Initialize `Orchestrator` instance
4. Execute query → Format results
5. Display output via Rich console

### Orchestrator Core (`orchestrator.py`)

**Technology**: Python 3.12+ with async/await

**Core Classes**:

```python
class OrchestratorConfig(BaseModel):
    """Immutable configuration."""
    model_config = ConfigDict(frozen=True)

    ollama_model: str = "qwen2.5:32b"
    ollama_host: str = "http://localhost:11434"
    max_iterations: int = 10
    max_context_tokens: int = 32000
    allowed_paths: list[Path] = [Path.home() / "projects"]
    log_level: str = "INFO"
    audit_log_path: Path = Path("./audit.jsonl")
    file_size_limit_mb: int = 10

class ToolCall(BaseModel):
    """Tool invocation request."""
    name: str
    arguments: dict[str, Any]

    @validator("name")
    def validate_tool_exists(cls, v: str) -> str:
        if v not in AVAILABLE_TOOLS:
            raise ValueError(f"Unknown tool: {v}")
        return v

class ToolResult(BaseModel):
    """Tool execution result."""
    success: bool
    output: str
    error: str | None = None
    execution_time_ms: float

class AgentState(BaseModel):
    """Mutable agent state."""
    messages: list[dict[str, Any]] = Field(default_factory=list)
    tool_calls_count: int = 0
    last_tool_result: ToolResult | None = None
    completed: bool = False
    iteration: int = 0
```

**Agent Loop Algorithm**:

```python
async def run_agent_loop(self, user_query: str) -> str:
    """Execute ReAct agent loop."""
    state = AgentState(messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query}
    ])

    while not state.completed and state.iteration < self.config.max_iterations:
        state.iteration += 1

        # PLANNING: LLM decides next action
        response = await self.ollama_client.chat(state.messages)

        # TOOL_CALL: Parse JSON if tool requested
        tool_call = self._parse_tool_call(response)
        if not tool_call:
            state.completed = True
            return response  # Final answer

        # EXECUTION: Run MCP tool with timeout
        tool_result = await self._execute_tool(tool_call)
        state.tool_calls_count += 1
        state.last_tool_result = tool_result

        # OBSERVATION: Add result to context
        state.messages.append({
            "role": "assistant",
            "content": f"Tool: {tool_call.name}\nArgs: {tool_call.arguments}"
        })
        state.messages.append({
            "role": "user",
            "content": f"Result: {tool_result.output}"
        })

        # REFLECTION: Loop continues automatically

    if not state.completed:
        raise MaxIterationsError(f"Agent didn't complete after {self.config.max_iterations} iterations")

    return state.messages[-1]["content"]
```

### MCP Server (`mcp_server/server.py`)

**Technology**: FastMCP

**Tool Implementation Pattern**:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("filesystem-server")

@mcp.tool(annotations={
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True
})
async def fs_read_file(path: str) -> str:
    """Read file content with size limit."""
    validated_path = await security.validate_path(path)

    file_size = validated_path.stat().st_size
    if file_size > config.file_size_limit_bytes:
        raise FileTooLargeError(f"File {file_size} bytes exceeds {config.file_size_limit_bytes}")

    async with aiofiles.open(validated_path, "r") as f:
        content = await f.read()

    await audit.log_operation("read", validated_path, success=True)
    return content

@mcp.tool(annotations={
    "readOnlyHint": False,
    "destructiveHint": True,
    "idempotentHint": False
})
async def fs_write_file(path: str, content: str) -> str:
    """Write content to file (create or overwrite)."""
    validated_path = await security.validate_path(path)

    # Confirmation for overwriting large files
    if validated_path.exists() and validated_path.stat().st_size > 1_000_000:
        if not await prompt_confirmation(f"Overwrite {validated_path}?"):
            return "Operation cancelled by user"

    async with aiofiles.open(validated_path, "w") as f:
        await f.write(content)

    await audit.log_operation("write", validated_path, success=True)
    return f"Written {len(content)} bytes to {validated_path}"
```

**Available Tools**:

| Tool | Read-Only | Destructive | Idempotent |
|------|-----------|-------------|------------|
| `fs_read_file` | ✅ | ❌ | ✅ |
| `fs_write_file` | ❌ | ✅ | ❌ |
| `fs_list_directory` | ✅ | ❌ | ✅ |
| `fs_create_directory` | ❌ | ❌ | ✅ |
| `fs_delete` | ❌ | ✅ | ❌ |
| `fs_move` | ❌ | ✅ | ❌ |
| `fs_copy` | ❌ | ❌ | ✅ |
| `fs_search` | ✅ | ❌ | ✅ |
| `fs_file_info` | ✅ | ❌ | ✅ |

### Security Module (`mcp_server/security.py`)

**Path Validation Algorithm**:

```python
async def validate_path(path: str, allowed_paths: list[Path]) -> Path:
    """Validate path is within allowed sandbox."""
    # Expand user home directory
    expanded = Path(path).expanduser()

    # Resolve to absolute path (follows symlinks)
    try:
        resolved = expanded.resolve(strict=False)
    except Exception as e:
        raise InvalidPathError(f"Cannot resolve path: {e}")

    # Check if within any allowed base path
    for allowed_base in allowed_paths:
        allowed_resolved = allowed_base.resolve()
        try:
            resolved.relative_to(allowed_resolved)
            return resolved  # Path is within allowed base
        except ValueError:
            continue  # Try next allowed base

    # No allowed base matched
    raise SecurityError(
        f"Path {resolved} is outside allowed paths: {allowed_paths}"
    )
```

**Security Tests** (adversarial inputs):

```python
# test_security.py
@pytest.mark.parametrize("malicious_path", [
    "../../etc/passwd",
    "/etc/passwd",
    "~/../../etc/passwd",
    "./symlink-to-etc",
    "projects/../../../etc/passwd"
])
async def test_path_traversal_blocked(malicious_path: str):
    with pytest.raises(SecurityError):
        await validate_path(malicious_path, allowed_paths=[Path.home() / "projects"])
```

### Ollama Client (`ollama_client/client.py`)

**Technology**: `ollama` Python library

**Wrapper Implementation**:

```python
class OllamaClient:
    """Wrapper for Ollama API with retry logic."""

    def __init__(self, model: str, host: str = "http://localhost:11434"):
        self.model = model
        self.client = ollama.Client(host=host)
        self._verify_model_available()

    def _verify_model_available(self) -> None:
        """Check model exists, pull if missing."""
        models = self.client.list()
        if self.model not in [m["name"] for m in models["models"]]:
            logger.warning(f"Model {self.model} not found, pulling...")
            self.client.pull(self.model)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(ollama.RequestError)
    )
    async def chat(
        self,
        messages: list[dict[str, Any]],
        stream: bool = False
    ) -> str:
        """Send chat request with retry logic."""
        try:
            response = self.client.chat(
                model=self.model,
                messages=messages,
                stream=stream
            )
            return response["message"]["content"]
        except ollama.ResponseError as e:
            logger.error(f"Ollama error: {e}")
            raise OllamaError(f"LLM request failed: {e}")
```

**System Prompt**:

```markdown
Sei un assistente AI con accesso al filesystem locale attraverso strumenti specifici.

## Strumenti Disponibili

Quando devi interagire con il filesystem, rispondi ESCLUSIVAMENTE con un JSON valido:
```json
{"tool": "nome_tool", "args": {"param1": "valore1"}}
```

### Tool Disponibili:
- `fs_read_file`: Legge un file. Args: {"path": "string"}
- `fs_write_file`: Scrive un file. Args: {"path": "string", "content": "string"}
- `fs_list_directory`: Lista directory. Args: {"path": "string", "recursive": bool}
- `fs_create_directory`: Crea directory. Args: {"path": "string"}
- `fs_delete`: Elimina file/dir. Args: {"path": "string", "force": bool}
- `fs_move`: Sposta/rinomina. Args: {"source": "string", "destination": "string"}
- `fs_copy`: Copia. Args: {"source": "string", "destination": "string"}
- `fs_search`: Cerca file. Args: {"pattern": "string", "path": "string", "content_match": "string"}
- `fs_file_info`: Info file. Args: {"path": "string"}

## Regole
1. Se la risposta richiede accesso al filesystem, usa SEMPRE un tool
2. Dopo aver ricevuto il risultato di un tool, analizzalo e decidi se serve altro
3. Quando hai tutte le informazioni, rispondi in linguaggio naturale
4. Mai inventare contenuti di file - usa sempre fs_read_file
5. Per operazioni distruttive, spiega cosa stai per fare

## Percorsi Consentiti
Puoi accedere solo a: {allowed_paths}
```

## Tech Stack

### Core Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| **Python** | 3.12+ | Modern type hints, async/await |
| **uv** | latest | Fast package management |
| **pydantic** | >= 2.0 | Data validation, settings |
| **typer** | >= 0.9 | CLI framework |
| **rich** | >= 13.0 | Terminal formatting |
| **ollama** | >= 0.1.0 | Ollama Python client |
| **mcp** | >= 0.1.0 | MCP SDK + FastMCP |
| **loguru** | >= 0.7 | Structured logging |
| **httpx** | >= 0.25 | Async HTTP (if needed) |
| **aiofiles** | >= 23.0 | Async file I/O |
| **tenacity** | >= 8.0 | Retry logic |

### Development Dependencies

| Library | Purpose |
|---------|---------|
| **pytest** | Testing framework |
| **pytest-asyncio** | Async test support |
| **pytest-cov** | Coverage reporting |
| **ruff** | Linting + formatting |
| **basedpyright** | Type checking |
| **pre-commit** | Git hooks |

## Data Models

### Configuration Model

```python
class OrchestratorConfig(BaseSettings):
    """Application settings (env vars + config file)."""
    model_config = SettingsConfigDict(
        env_prefix="OLLAMA_FS_",
        env_file="~/.ollama-fs/.env"
    )

    ollama_model: str = Field(default="qwen2.5:32b")
    ollama_host: HttpUrl = Field(default="http://localhost:11434")
    max_iterations: PositiveInt = Field(default=10)
    max_context_tokens: PositiveInt = Field(default=32000)
    allowed_paths: list[DirectoryPath] = Field(default_factory=lambda: [Path.home() / "projects"])
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")
    audit_log_path: FilePath = Field(default=Path("./audit.jsonl"))
    file_size_limit_mb: PositiveInt = Field(default=10)

    @property
    def file_size_limit_bytes(self) -> int:
        return self.file_size_limit_mb * 1024 * 1024
```

### Tool Models

```python
class FileInfo(BaseModel):
    """File metadata."""
    path: Path
    size_bytes: int
    modified_at: datetime
    is_directory: bool
    permissions: str
    owner: str | None = None

class DirectoryListing(BaseModel):
    """Directory contents."""
    path: Path
    items: list[FileInfo]
    total_items: int

class SearchResult(BaseModel):
    """File search result."""
    path: Path
    match_type: Literal["name", "content"]
    line_number: int | None = None  # For content matches
    snippet: str | None = None
```

## Deployment

### Installation

```bash
# Install globally via uv
uv tool install ollama-mcp-orchestrator

# Or install in virtual environment
uv venv
uv pip install ollama-mcp-orchestrator
```

### Configuration

```bash
# Create config directory
mkdir -p ~/.ollama-fs

# Create config file
cat > ~/.ollama-fs/config.yaml <<EOF
ollama_model: qwen2.5:32b
allowed_paths:
  - ~/projects
  - ~/documents
max_iterations: 15
log_level: INFO
EOF
```

### First Run

```bash
# Verify Ollama is running
ollama list

# Pull model if needed
ollama pull qwen2.5:32b

# Start chat session
ollama-fs chat
```

## Architecture Decision Records

See `docs/ADR/` for detailed decisions:

- **ADR-001**: Why FastMCP over custom MCP implementation
- **ADR-002**: Why Pydantic v2 over dataclasses
- **ADR-003**: Why async/await for file I/O
- **ADR-004**: Why JSONL for audit log (not SQLite)
- **ADR-005**: Why Typer over Click for CLI

## Security Architecture

### Threat Model

**In Scope**:
- Path traversal attacks → MITIGATED by `validate_path()`
- Accidental file deletion → MITIGATED by confirmation prompts
- Large file DoS → MITIGATED by file size limits

**Out of Scope**:
- Network attacks (tool is local-only)
- Code execution (LLM doesn't execute code)
- Data exfiltration (no network access)

### Defense in Depth

```
Layer 1: Path Validation → Reject invalid/malicious paths
Layer 2: Sandbox Enforcement → Restrict to ALLOWED_PATHS
Layer 3: Confirmation Prompts → User approval for destructive ops
Layer 4: Audit Logging → Forensic trail of all operations
Layer 5: File Size Limits → Prevent resource exhaustion
```

## Performance Considerations

### Latency Budget

```
Total Response Time = LLM Inference + Tool Execution + Overhead

Target: < 2s for simple queries

Breakdown:
- LLM Inference (Qwen2.5:32b): ~500-1000ms
- Tool Execution: < 100ms (see NFR-001)
- Overhead (parsing, logging): < 50ms
```

### Optimization Strategies

1. **Async I/O**: Use `aiofiles` for non-blocking file operations
2. **Lazy Loading**: Import modules only when needed
3. **Result Streaming**: Stream LLM responses (v0.2.0)
4. **Tool Caching**: LRU cache for idempotent tools (v0.2.0)

## Scalability (Future)

**v0.1.0**: Single-user, single-process

**v0.2.0+**: Potential enhancements:
- Multi-conversation support (parallel sessions)
- Distributed MCP servers (remote filesystem access)
- Horizontal scaling (multiple Ollama instances)

Not needed for MVP - local tool optimized for single user.
