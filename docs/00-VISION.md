# Vision & Strategy

> **Documento storico (gennaio 2026), superato il 2026-08-16.**
> La visione qui descritta non è più valida: ogni componente prevista è oggi
> disponibile come software installabile in un comando. La decisione di
> chiusura, con le alternative valutate e i criteri per riaprirla, è in
> [ARC-002](architecture/ARC-002.closure-decision.md); le misure che l'hanno
> motivata in [09-SPIKE-MCP-GUARDRAILS.md](09-SPIKE-MCP-GUARDRAILS.md).
>
> Il paragrafo *Competitors* qui sotto è istruttivo per come ha sbagliato:
> elencava LangChain e AutoGPT, e non contemplava che il concorrente vero
> sarebbe stato Ollama stesso.

## Project Overview

**Ollama-MCP Filesystem Orchestrator** is a production-grade Python orchestrator that enables local Ollama models to securely access the filesystem through the Model Context Protocol (MCP). It acts as an intelligent bridge between Ollama and MCP tools, managing the complete tool calling lifecycle with planning, execution, and reflection.

## Elevator Pitch

A Python orchestrator that lets local LLMs (Qwen, Llama) safely interact with your filesystem through MCP, featuring agent loop planning, security sandboxing, and comprehensive audit logging. Think "ReAct agent for file operations" with production-grade safety.

## Target Users

### Primary Persona: AI Developer (Claudio)
- **Profile**: Python developer working with local LLMs on Mac Studio M2 Ultra + Debian laptop
- **Pain Points**:
  - Ollama models can't directly access filesystem
  - Manual tool calling is tedious and error-prone
  - Need security sandbox to prevent accidental damage
  - Require audit trail for debugging
- **Goals**:
  - Automate file operations via natural language
  - Maintain full control over allowed paths
  - Track all filesystem modifications
  - Use offline (no API costs)

### Secondary Persona: DevOps Engineer
- **Profile**: Uses LLMs for infrastructure automation
- **Pain Points**: Need safe filesystem access for log analysis, config management
- **Goals**: Automated file search, content extraction, safe modifications

## Value Proposition

**Why choose this over direct MCP usage?**
- **Agent Loop**: Automatic planning → execution → reflection (ReAct pattern)
- **Security First**: Path sandboxing, traversal prevention, destructive operation confirmation
- **Full Observability**: Structured logging, JSONL audit trail, execution metrics
- **Production Ready**: Type-safe (Pydantic v2), tested (>80% coverage), documented

## Business Model

**Open Source (MIT License)**
- Free for all use cases
- Community-driven development
- GitHub-based collaboration

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Tool Call Success Rate | > 95% | Successful executions / total calls |
| Average Latency | < 100ms | Tool execution time (excluding LLM) |
| Security Incidents | 0 | Path traversal attempts blocked |
| User Adoption | 100+ GitHub stars | 6 months post-release |
| Test Coverage | > 80% | line coverage |

## MVP Scope (v0.1.0)

**Must Have**:
- ✅ 9 filesystem tools (read, write, list, create_dir, delete, move, copy, search, file_info)
- ✅ Agent loop with planning/execution/reflection
- ✅ Typer CLI (chat mode, ask mode, config)
- ✅ Security sandbox (ALLOWED_PATHS validation)
- ✅ Audit logging (JSONL format)
- ✅ Ollama integration (Qwen2.5:32b, Llama3.3:70b)

**Nice to Have** (v0.2.0+):
- Streaming responses from Ollama
- LRU cache for tool results
- Prometheus metrics export
- Multi-conversation support

## Future Vision

### 1 Year
- **Multi-Model Support**: Support for OpenAI, Anthropic (via MCP)
- **Advanced Tools**: Git operations, Docker interaction, database queries
- **Web UI**: Simple web interface for non-CLI users
- **Plugin System**: Custom tool registration

### 3 Years
- **Enterprise Features**: Team collaboration, role-based access
- **Cloud Deployment**: SaaS offering for teams
- **Ecosystem**: Marketplace for community tools

## Constraints

### Technical
- **OS**: macOS (Apple Silicon) + Debian Linux
- **Python**: 3.12+ (for modern type hints)
- **Package Manager**: uv (fast, reliable)
- **Models**: Ollama-compatible only (local deployment)

### Resource
- **Budget**: $0 (open source, local compute)
- **Timeline**: MVP in 2-3 weeks
- **Team**: Solo developer (Claudio)

### Scope
- **No cloud deployment**: Local-first tool
- **No GUI**: CLI only for MVP
- **English only**: No i18n for MVP

## Competitors

| Competitor | Strengths | Weaknesses |
|------------|-----------|------------|
| **Direct MCP** | Official protocol | No agent loop, manual tool calling |
| **LangChain Agents** | Rich ecosystem | Heavyweight, cloud-focused |
| **AutoGPT** | Full autonomy | No MCP support, requires API keys |
| **Ollama-Python** | Direct integration | No tool calling orchestration |

## Unique Differentiator

**Why Ollama-MCP Orchestrator wins**:
1. **Local-First**: 100% offline, no API costs, full privacy
2. **MCP Native**: Uses official protocol, future-proof
3. **Security Focused**: Sandbox, audit, confirmation for destructive ops
4. **Production Grade**: Type-safe, tested, logged, documented
5. **Agent Loop**: Automatic planning/reflection (not just tool execution)

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Path traversal exploit | HIGH | LOW | Comprehensive path validation tests |
| Ollama model hallucination | MEDIUM | MEDIUM | Strict JSON parsing, fallback prompts |
| Performance degradation | LOW | LOW | Async I/O, timeout limits |
| User adoption | MEDIUM | MEDIUM | Clear docs, working examples |

## Definition of Success

**v0.1.0 Release Criteria**:
- ✅ All 9 tools implemented and tested
- ✅ Agent loop completes 3-step tasks (read → analyze → write)
- ✅ Security tests pass (no path traversal)
- ✅ Documentation complete (README + examples)
- ✅ Test coverage > 80%
- ✅ Successfully runs on Mac + Debian

**Community Success**:
- 100+ GitHub stars within 6 months
- 10+ external contributors
- Featured in Awesome-Ollama list
