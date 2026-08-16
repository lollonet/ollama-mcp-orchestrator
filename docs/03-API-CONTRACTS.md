# API Contracts & Interfaces

> **Documento storico (gennaio 2026), superato il 2026-08-16.** Il progetto
> non viene implementato: vedi [ARC-002](architecture/ARC-002.closure-decision.md)
> e lo [spike sui guardrail MCP](09-SPIKE-MCP-GUARDRAILS.md).


## MCP Tool Contracts

All MCP tools follow a standard contract pattern with Pydantic validation.

### Tool Response Format

```python
class ToolResponse(BaseModel):
    """Standard response from all tools."""
    success: bool
    output: str
    error: str | None = None
    execution_time_ms: float
    metadata: dict[str, Any] = Field(default_factory=dict)
```

### Filesystem Tools API

#### fs_read_file

**Description**: Read file content with size limit

**Input**:
```python
class ReadFileArgs(BaseModel):
    path: str  # Relative or absolute path (will be validated)
```

**Output**:
```python
{
    "success": true,
    "output": "<file content>",
    "execution_time_ms": 12.5,
    "metadata": {
        "size_bytes": 1024,
        "encoding": "utf-8"
    }
}
```

**Errors**:
- `FileNotFoundError`: Path doesn't exist
- `FileTooLargeError`: File exceeds size limit (10MB default)
- `SecurityError`: Path outside allowed sandbox
- `PermissionError`: No read permission

**Example**:
```json
{
    "tool": "fs_read_file",
    "args": {"path": "~/projects/myapp/config.yaml"}
}
```

---

#### fs_write_file

**Description**: Write content to file (create or overwrite)

**Input**:
```python
class WriteFileArgs(BaseModel):
    path: str
    content: str
    create_parents: bool = Field(default=True)  # Create intermediate directories
```

**Output**:
```python
{
    "success": true,
    "output": "Written 1024 bytes to /Users/claudio/projects/test.py",
    "execution_time_ms": 15.3
}
```

**Errors**:
- `SecurityError`: Path outside allowed sandbox
- `PermissionError`: No write permission
- `OSError`: Disk full or other filesystem error

**Confirmation Required**: Yes, if overwriting file > 1MB

---

#### fs_list_directory

**Description**: List directory contents with metadata

**Input**:
```python
class ListDirectoryArgs(BaseModel):
    path: str
    recursive: bool = Field(default=False)
    include_hidden: bool = Field(default=False)
    max_depth: int = Field(default=10)  # Max recursion depth
```

**Output**:
```python
{
    "success": true,
    "output": "Found 15 items in /Users/claudio/projects/myapp",
    "metadata": {
        "items": [
            {
                "path": "config.yaml",
                "type": "file",
                "size_bytes": 1024,
                "modified_at": "2026-01-21T10:30:00Z"
            },
            {
                "path": "src/",
                "type": "directory",
                "items": 8
            }
        ],
        "total_items": 15
    }
}
```

---

#### fs_create_directory

**Description**: Create directory including intermediate directories

**Input**:
```python
class CreateDirectoryArgs(BaseModel):
    path: str
    mode: int = Field(default=0o755)  # Unix permissions
```

**Output**:
```python
{
    "success": true,
    "output": "Created directory /Users/claudio/projects/newdir",
    "execution_time_ms": 5.2
}
```

**Idempotent**: Yes (no error if directory already exists)

---

#### fs_delete

**Description**: Delete file or directory

**Input**:
```python
class DeleteArgs(BaseModel):
    path: str
    force: bool = Field(default=False)  # Delete non-empty directories
```

**Output**:
```python
{
    "success": true,
    "output": "Deleted /Users/claudio/projects/old_file.txt",
    "execution_time_ms": 8.1
}
```

**Confirmation Required**: Yes, if deleting non-empty directory (unless `force=True`)

**Errors**:
- `FileNotFoundError`: Path doesn't exist
- `DirectoryNotEmptyError`: Non-empty directory without `force=True`

---

#### fs_move

**Description**: Move or rename file/directory

**Input**:
```python
class MoveArgs(BaseModel):
    source: str
    destination: str
    overwrite: bool = Field(default=False)
```

**Output**:
```python
{
    "success": true,
    "output": "Moved /path/source to /path/dest",
    "execution_time_ms": 10.5
}
```

**Confirmation Required**: Yes, if destination exists (unless `overwrite=True`)

---

#### fs_copy

**Description**: Copy file or directory

**Input**:
```python
class CopyArgs(BaseModel):
    source: str
    destination: str
    recursive: bool = Field(default=True)  # For directories
```

**Output**:
```python
{
    "success": true,
    "output": "Copied /path/source to /path/dest (1024 bytes)",
    "execution_time_ms": 18.3
}
```

---

#### fs_search

**Description**: Search files by glob pattern or content

**Input**:
```python
class SearchArgs(BaseModel):
    pattern: str | None = None  # Glob pattern (e.g., "*.py")
    content_match: str | None = None  # Regex pattern for content
    path: str = Field(default=".")  # Starting directory
    max_results: int = Field(default=1000)
    case_sensitive: bool = Field(default=False)
```

**Output**:
```python
{
    "success": true,
    "output": "Found 8 matches",
    "metadata": {
        "matches": [
            {
                "path": "/Users/claudio/projects/myapp/main.py",
                "match_type": "name",
                "size_bytes": 2048
            },
            {
                "path": "/Users/claudio/projects/myapp/utils.py",
                "match_type": "content",
                "line_number": 42,
                "snippet": "def process_data():"
            }
        ],
        "total_matches": 8,
        "truncated": false
    }
}
```

**Timeout**: 30 seconds (returns partial results if exceeded)

---

#### fs_file_info

**Description**: Get detailed file metadata

**Input**:
```python
class FileInfoArgs(BaseModel):
    path: str
```

**Output**:
```python
{
    "success": true,
    "output": "File info for /path/to/file.py",
    "metadata": {
        "path": "/Users/claudio/projects/myapp/main.py",
        "size_bytes": 2048,
        "size_human": "2.0 KB",
        "modified_at": "2026-01-21T10:30:00Z",
        "created_at": "2026-01-15T09:00:00Z",
        "is_directory": false,
        "permissions": "rw-r--r--",
        "owner": "claudio",
        "mime_type": "text/x-python"
    }
}
```

---

## CLI Interface Contracts

### chat Command

```bash
ollama-fs chat [OPTIONS]
```

**Options**:
- `--model TEXT`: Ollama model name (default: qwen2.5:32b)
- `--allowed-paths PATH`: Add allowed base path (repeatable)
- `--verbose / --no-verbose`: Enable debug logging
- `--json-logs`: Output logs as JSON
- `--config PATH`: Config file path (default: ~/.ollama-fs/config.yaml)

**Interactive Commands**:
- `/help`: Show available commands
- `/history`: Show conversation history
- `/clear`: Clear conversation
- `/exit` or `Ctrl+D`: Exit chat mode

**Example Session**:
```
$ ollama-fs chat --verbose
🤖 Ollama MCP Orchestrator v0.1.0
📁 Allowed paths: ~/projects
🔧 Model: qwen2.5:32b

You: List all Python files in ~/projects/myapp

[DEBUG] Tool call: fs_search(pattern="*.py", path="~/projects/myapp")
[DEBUG] Tool result: Found 8 Python files in 15.3ms