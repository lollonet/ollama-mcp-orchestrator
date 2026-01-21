# Vision

## What this project does

Python orchestrator that connects local Ollama models to the filesystem through the Model Context Protocol (MCP). Manages the complete tool calling lifecycle: planning, execution, reflection.

## Why it exists

**Problem**: Ollama models can't access files directly. Manually calling MCP tools is tedious and risky.

**Solution**: Autonomous agent loop that plans filesystem tasks, executes tools safely, and tracks all changes.

## Who uses it

Python developers working with local LLMs who need:
- Automated file operations via natural language
- Security sandbox to prevent accidents
- Audit trail for debugging
- Offline operation (no API costs)

## What makes it different

- **Agent loop**: Automatic planning/execution/reflection (not just tool calling)
- **Security focused**: Path sandboxing, confirmation prompts, audit logging
- **Type-safe**: Pydantic v2 validation, basedpyright strict mode
- **Local-first**: Works offline, no cloud dependencies

## Success criteria

- Tool calls succeed > 95% of the time
- Tool execution < 100ms (excluding LLM inference)
- No successful path traversal attacks
- Test coverage > 80%

## MVP Scope (v0.1.0)

Core features:
- 9 filesystem tools (read, write, list, create_dir, delete, move, copy, search, file_info)
- Agent loop with ReAct pattern
- Typer CLI (chat and ask modes)
- Security sandbox with path validation
- JSONL audit logging
- Ollama integration (tested with Qwen2.5:32b, Llama3.3:70b)

Later versions:
- Streaming responses
- Tool result caching
- Multi-conversation support

## Technical constraints

- **OS**: macOS (Apple Silicon) + Debian Linux
- **Python**: 3.12+ (modern type hints)
- **Package Manager**: uv
- **Models**: Ollama-compatible only

## Scope limits

- CLI only for v0.1.0 (no GUI)
- Local-first (no cloud deployment)
- Single-user (no authentication/multi-tenancy)

## Risks

- **Path traversal**: Mitigated with comprehensive validation tests
- **Model hallucination**: Mitigated with strict JSON parsing
- **Performance issues**: Mitigated with async I/O and timeouts

## v0.1.0 Release criteria

- All 9 tools implemented and tested
- Agent loop completes multi-step tasks
- Security tests pass
- Documentation complete
- Test coverage > 80%
- Works on macOS and Debian
