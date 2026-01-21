# Requirements Index

## Overview

This document tracks all functional and non-functional requirements for the Ollama-MCP Filesystem Orchestrator.

## Functional Requirements

| ID | Domain | Title | Status | Priority |
|----|--------|-------|--------|----------|
| [REQ-001](REQ-001.md) | filesystem-tools | Filesystem Tools | draft | P0 |
| [REQ-002](REQ-002.md) | agent-loop | Agent Loop (ReAct Pattern) | draft | P0 |
| [REQ-003](REQ-003.md) | user-interface | CLI Interface | draft | P0 |
| [REQ-004](REQ-004.md) | security | Security Sandbox | draft | P0 |
| [REQ-005](REQ-005.md) | logging-audit | Audit Logging | draft | P1 |
| [REQ-006](REQ-006.md) | integration | Ollama Integration | draft | P0 |
| [REQ-007](REQ-007.md) | state-management | Conversation Management | draft | P2 |
| [REQ-008](REQ-008.md) | error-handling | Error Handling | draft | P1 |
| [REQ-009](REQ-009.md) | configuration | Configuration Management | draft | P2 |

## Requirements by Domain

### filesystem-tools
- REQ-001: 9 core filesystem operations via MCP

### agent-loop
- REQ-002: Autonomous ReAct agent loop with planning/reflection

### user-interface
- REQ-003: Typer CLI with chat and ask modes

### security
- REQ-004: Path sandbox with validation and confirmation prompts

### logging-audit
- REQ-005: JSONL audit trail for all destructive operations

### integration
- REQ-006: Ollama Python client with retry logic

### state-management
- REQ-007: In-memory conversation history with context window management

### error-handling
- REQ-008: Comprehensive error handling with actionable messages

### configuration
- REQ-009: YAML config + env vars + CLI overrides

## Requirements by Priority

### P0 (Critical - MVP Blockers)
- REQ-001: Filesystem Tools
- REQ-002: Agent Loop
- REQ-003: CLI Interface
- REQ-004: Security Sandbox
- REQ-006: Ollama Integration

### P1 (High - Important for v0.1.0)
- REQ-005: Audit Logging
- REQ-008: Error Handling

### P2 (Medium - Nice to have for v0.1.0)
- REQ-007: Conversation Management
- REQ-009: Configuration Management

### P3 (Low - Future versions)
- None currently defined

## Requirements by Status

### draft (9)
All requirements currently in draft status pending implementation and validation.

### approved (0)
No requirements approved yet.

### implemented (0)
No requirements implemented yet.

## Traceability Matrix

| Requirement | WBS Tasks | Test Files | Source Files |
|-------------|-----------|------------|--------------|
| REQ-001 | WBS-004, WBS-005 | test_tools_*.py | mcp_server/tools/filesystem.py |
| REQ-002 | WBS-007 | test_orchestrator.py | orchestrator.py |
| REQ-003 | WBS-008 | test_cli.py | cli.py |
| REQ-004 | WBS-003, WBS-010 | test_security*.py | mcp_server/security.py |
| REQ-005 | WBS-009 | test_audit.py | utils/audit.py |
| REQ-006 | WBS-006 | test_ollama_client.py | ollama_client/client.py |
| REQ-007 | WBS-007 | test_orchestrator.py | orchestrator.py |
| REQ-008 | All tasks | test_*.py | All modules |
| REQ-009 | WBS-002 | test_config.py | config.py |

## Related Documentation

- [00-VISION.md](../00-VISION.md) - Project vision and goals
- [01-REQUIREMENTS.md](../01-REQUIREMENTS.md) - Detailed requirements specification
- [02-ARCHITECTURE.md](../02-ARCHITECTURE.md) - System architecture
- [08-WBS.md](../08-WBS.md) - Work breakdown structure

## Change Log

| Date | Author | Change |
|------|--------|--------|
| 2026-01-21 | Claude | Initial requirements extracted from interview |

## Notes

- All requirements currently in draft status
- Requirements will be updated to approved status after stakeholder review
- Implementation progress tracked via WBS tasks in 08-WBS.md
