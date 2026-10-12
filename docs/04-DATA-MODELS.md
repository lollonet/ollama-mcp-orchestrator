# Data Models

> **Documento storico (gennaio 2026), superato il 2026-08-16.** Il progetto
> non viene implementato: vedi [ARC-002](architecture/ARC-002.closure-decision.md)
> e lo [spike sui guardrail MCP](09-SPIKE-MCP-GUARDRAILS.md).


## Core Domain Models

All models use Pydantic v2 for validation and serialization.

### Configuration Models

```python
class OrchestratorConfig(BaseSettings):
    """Application configuration (env vars + config file)."""
    model_config = SettingsConfigDict(
        env_prefix="OLLAMA_FS_",
        env_file="~/.ollama-fs/.env",
        frozen=True  # Immutable after creation
    )

    ollama_model: str = Field(default="qwen2.5:32b")
    ollama_host: HttpUrl = Field(default="http://localhost:11434")
    max_iterations: PositiveInt = Field(default=10, ge=1, le=50)
    max_context_tokens: PositiveInt = Field(default=32000, ge=1000, le=128000)
    allowed_paths: list[DirectoryPath] = Field(default_factory=lambda: [Path.home() / "projects"])
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")
    audit_log_path: FilePath = Field(default=Path("./audit.jsonl"))
    file_size_limit_mb: PositiveInt = Field(default=10, ge=1, le=100)
    search_timeout_seconds: PositiveInt = Field(default=30)

    @field_validator("allowed_paths")
    @classmethod
    def validate_paths_exist(cls, v: list[Path]) -> list[Path]:
        """Ensure all allowed paths exist and are absolute."""
        for path in v:
            if not path.exists():
                raise ValueError(f"Allowed path does not exist: {path}")
            if not path.is_absolute():
                raise ValueError(f"Allowed path must be absolute: {path}")
        return v
```

### Agent State Models

```python
class ToolCall(BaseModel):
    """Represents a tool invocation request."""
    name: str
    arguments: dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("name")
    @classmethod
    def validate_tool_exists(cls, v: str) -> str:
        """Ensure tool name is valid."""
        valid_tools = {
            "fs_read_file", "fs_write_file", "fs_list_directory",
            "fs_create_directory", "fs_delete", "fs_move",
            "fs_copy", "fs_search", "fs_file_info"
        }
        if v not in valid_tools:
            raise ValueError(f"Unknown tool: {v}")
        return v

class ToolResult(BaseModel):
    """Result of tool execution."""
    success: bool
    output: str
    error: str | None = None
    execution_time_ms: float
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Message(BaseModel):
    """Chat message."""
    role: Literal["system", "user", "assistant"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tool_call: ToolCall | None = None
    tool_result: ToolResult | None = None

class AgentState(BaseModel):
    """Mutable state of agent loop."""
    messages: list[Message] = Field(default_factory=list)
    tool_calls_count: int = Field(default=0, ge=0)
    last_tool_result: ToolResult | None = None
    completed: bool = Field(default=False)
    iteration: int = Field(default=0, ge=0)
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    def add_user_message(self, content: str) -> None:
        """Add user message to history."""
        self.messages.append(Message(role="user", content=content))

    def add_assistant_message(self, content: str, tool_call: ToolCall | None = None) -> None:
        """Add assistant message to history."""
        self.messages.append(Message(
            role="assistant",
            content=content,
            tool_call=tool_call
        ))

    def add_tool_result(self, result: ToolResult) -> None:
        """Record tool execution result."""
        self.last_tool_result = result
        self.tool_calls_count += 1
        if self.messages:
            self.messages[-1].tool_result = result
```

### Filesystem Models

```python
class FileInfo(BaseModel):
    """File/directory metadata."""
    path: Path
    name: str
    size_bytes: int
    size_human: str  # Computed field: "1.5 MB"
    modified_at: datetime
    created_at: datetime | None = None
    is_directory: bool
    is_symlink: bool = False
    permissions: str  # Unix format: "rw-r--r--"
    owner: str | None = None
    mime_type: str | None = None

    @computed_field
    @property
    def size_human(self) -> str:
        """Human-readable file size."""
        for unit in ["B", "KB", "MB", "GB"]:
            if self.size_bytes < 1024:
                return f"{self.size_bytes:.1f} {unit}"
            self.size_bytes /= 1024
        return f"{self.size_bytes:.1f} TB"

    @classmethod
    def from_path(cls, path: Path) -> "FileInfo":
        """Create FileInfo from Path object."""
        stat = path.stat()
        return cls(
            path=path,
            name=path.name,
            size_bytes=stat.st_size,
            modified_at=datetime.fromtimestamp(stat.st_mtime),
            created_at=datetime.fromtimestamp(stat.st_ctime),
            is_directory=path.is_dir(),
            is_symlink=path.is_symlink(),
            permissions=oct(stat.st_mode)[-3:],
            owner=pwd.getpwuid(stat.st_uid).pw_name if hasattr(pwd, "getpwuid") else None
        )

class DirectoryListing(BaseModel):
    """Directory contents."""
    path: Path
    items: list[FileInfo]
    total_items: int
    total_size_bytes: int
    subdirectories: int
    files: int

    @computed_field
    @property
    def total_size_human(self) -> str:
        """Human-readable total size."""
        return FileInfo(path=Path("."), size_bytes=self.total_size_bytes).size_human

class SearchMatch(BaseModel):
    """File search result."""
    path: Path
    match_type: Literal["name", "content"]
    line_number: int | None = None  # For content matches
    snippet: str | None = None
    score: float = Field(default=1.0, ge=0.0, le=1.0)  # Relevance score

class SearchResult(BaseModel):
    """Collection of search matches."""
    query: str
    matches: list[SearchMatch]
    total_matches: int
    truncated: bool  # True if max_results reached
    execution_time_ms: float
```

### Audit Models

```python
class AuditLogEntry(BaseModel):
    """Single audit log entry."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: str
    action: Literal["read", "write", "delete", "move", "copy", "create_dir", "search", "list"]
    tool: str
    path: str
    user: str
    success: bool
    error: str | None = None
    execution_time_ms: float
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_jsonl(self) -> str:
        """Serialize to JSONL format."""
        return self.model_dump_json() + "\n"

    @classmethod
    def from_jsonl(cls, line: str) -> "AuditLogEntry":
        """Deserialize from JSONL format."""
        return cls.model_validate_json(line)
```

## Relationship Diagram

```
OrchestratorConfig (1) ──┐
                         │
                         ├──> Orchestrator (1)
                         │
AgentState (1) ──────────┘
   │
   ├─> Message (*)
   │     ├─> ToolCall (0..1)
   │     └─> ToolResult (0..1)
   │
   └─> ToolResult (0..1) ──> AuditLogEntry (1)

FileInfo (*)
   └─> DirectoryListing (1)

SearchMatch (*)
   └─> SearchResult (1)
```

## State Transitions

### AgentState Lifecycle

```
INITIAL
   │
   ├─> add_user_message()
   │
   v
PLANNING (iteration++)
   │
   ├─> LLM decides: Tool needed?
   │
   ├─> YES: parse ToolCall
   │     │
   │     ├─> add_assistant_message(tool_call)
   │     │
   │     v
   │   EXECUTING
   │     │
   │     ├─> Execute tool → ToolResult
   │     │
   │     ├─> add_tool_result()
   │     │
   │     └─> Back to PLANNING
   │
   └─> NO: Final answer
         │
         ├─> completed = True
         │
         v
       COMPLETED
```

## Validation Rules

### Path Validation

```python
# All path inputs must pass:
1. Expand user (~) → Path.expanduser()
2. Resolve to absolute → Path.resolve()
3. Check within allowed_paths → validate_path()
4. Check exists (if required) → Path.exists()
5. Check permissions → os.access()
```

### File Size Validation

```python
# Before reading files:
if file_size > config.file_size_limit_bytes:
    raise FileTooLargeError(
        f"File {file_size} bytes exceeds limit {config.file_size_limit_bytes}"
    )
```

### Tool Argument Validation

```python
# All tool args validated via Pydantic:
class ReadFileArgs(BaseModel):
    path: str  # Not empty

    @field_validator("path")
    @classmethod
    def validate_path_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Path cannot be empty")
        return v.strip()
```

## Computed Fields

### Size Formatting

```python
@computed_field
@property
def size_human(self) -> str:
    """Human-readable size (e.g., '1.5 MB')."""
    units = ["B", "KB", "MB", "GB", "TB"]
    size = self.size_bytes
    for unit in units:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"
```

### Execution Metrics

```python
@computed_field
@property
def average_tool_latency(self) -> float:
    """Average tool execution time in ms."""
    if self.tool_calls_count == 0:
        return 0.0
    total_time = sum(
        msg.tool_result.execution_time_ms
        for msg in self.messages
        if msg.tool_result
    )
    return total_time / self.tool_calls_count
```

## Domain Events (Future)

For v0.2.0, consider event-driven architecture:

```python
class DomainEvent(BaseModel):
    """Base class for domain events."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: str

class ToolExecutedEvent(DomainEvent):
    """Emitted after tool execution."""
    event_type: Literal["tool_executed"] = "tool_executed"
    tool_name: str
    success: bool
    execution_time_ms: float

class AgentLoopCompletedEvent(DomainEvent):
    """Emitted when agent loop finishes."""
    event_type: Literal["agent_loop_completed"] = "agent_loop_completed"
    total_iterations: int
    total_tool_calls: int
```
