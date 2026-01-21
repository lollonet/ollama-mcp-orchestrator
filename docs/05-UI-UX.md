# UI/UX Design (CLI)

## Design Philosophy

**Principle**: Command-line first, optimized for developer workflows.

- **Simplicity**: Single command to start (`ollama-fs chat`)
- **Discoverability**: `--help` at every level
- **Feedback**: Rich formatting for readability
- **Safety**: Confirmation prompts for destructive operations

## CLI Interface Design

### Primary Commands

```
ollama-fs
├── chat              # Interactive REPL mode
├── ask               # Single query mode
└── config            # Configuration management
    ├── show          # Display current config
    └── set           # Update config value
```

### Terminal UI Components (Rich)

#### 1. Welcome Banner

```
┌────────────────────────────────────────────────┐
│  🤖 Ollama MCP Filesystem Orchestrator v0.1.0  │
│                                                │
│  📁 Allowed paths: ~/projects, ~/documents     │
│  🔧 Model: qwen2.5:32b                         │
│  💾 Audit log: ~/.ollama-fs/audit.jsonl        │
└────────────────────────────────────────────────┘
```

#### 2. Input Prompt

```
You: <cursor here>
```

#### 3. Tool Call Display (Verbose Mode)

```
[Tool] fs_read_file
├─ path: ~/projects/myapp/config.yaml
└─ ⏱  12.5ms

[Result] ✓ Success
├─ size: 1.2 KB
└─ content: <truncated preview>
```

#### 4. Progress Indicators

```
Searching files... ━━━━━━━━━━━━━━━━━━━━━━━━ 100% (1,234 files scanned)
```

#### 5. Confirmation Prompts

```
⚠️  Warning: About to delete non-empty directory
   Path: ~/projects/old-project (15 files)

   Continue? [y/N]:
```

#### 6. Error Messages

```
❌ Error: Path outside allowed sandbox

   Attempted path: /etc/passwd
   Allowed paths:
     • ~/projects
     • ~/documents

   💡 Tip: Add allowed paths with --allowed-paths flag
```

#### 7. Results Table (for listings)

```
┌────────────────────┬────────┬──────────────────────┐
│ Name               │ Size   │ Modified             │
├────────────────────┼────────┼──────────────────────┤
│ config.yaml        │ 1.2 KB │ 2026-01-21 10:30:00  │
│ main.py            │ 4.5 KB │ 2026-01-20 15:45:00  │
│ README.md          │ 2.1 KB │ 2026-01-19 09:00:00  │
└────────────────────┴────────┴──────────────────────┘
```

## Interactive Chat Mode

### User Flow

```
1. START → Welcome banner
2. PROMPT → "You: " with autocomplete
3. INPUT → User types natural language query
4. PROCESSING → Show spinner/progress
5. TOOL CALLS → Display in verbose mode
6. RESULT → Formatted response
7. LOOP → Back to step 2
```

### Example Session

```bash
$ ollama-fs chat

┌────────────────────────────────────────────────┐
│  🤖 Ollama MCP Orchestrator v0.1.0              │
│  📁 Allowed: ~/projects                        │
│  🔧 Model: qwen2.5:32b                         │
└────────────────────────────────────────────────┘

Type /help for commands, Ctrl+D to exit

You: List all Python files in ~/projects/myapp

[Tool] fs_search
├─ pattern: *.py
├─ path: ~/projects/myapp
└─ ⏱  15.3ms

[Result] ✓ Found 8 files