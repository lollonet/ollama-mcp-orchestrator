# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0-closed] - 2026-08-16

### Changed
- **Progetto chiuso.** La v0.1.0 non verrà implementata: fra la specifica
  (gennaio 2026) e oggi l'ecosistema ha assorbito ogni componente prevista.
  Decisione, alternative valutate e criteri di riapertura in
  `docs/architecture/ARC-002.closure-decision.md`.
- Tutti i REQ-001..REQ-009 passati a `superseded`; documenti di specifica
  marcati come storici e lasciati leggibili.
- README riscritto come registro della decisione.

### Added
- `docs/09-SPIKE-MCP-GUARDRAILS.md`: spike comparativo su mcp-firewall 0.1.0 e
  airlock 0.2.38, con misure della postura di fallimento di entrambi.
- `spike/`: artefatti riproducibili dei due spike (server di prova, policy,
  sonde).
- `examples/airlock.recommended.yaml`: configurazione di partenza per il
  guardrail adottato al posto di questo progetto.

### Security
- Rilevati e documentati tre fallimenti in apertura in mcp-firewall 0.1.0:
  approvazione umana auto-consentita fuori da un TTY, traversal `../` che buca
  le allow-list, metodi diversi da `tools/call` non ispezionati.
- Rilevata in airlock 0.2.38 la stessa debolezza sul matching dei path
  (nessuna normalizzazione), con punto d'innesto identificato per il fix.

## [Non implementato] - specifica di gennaio 2026

### Planned for v0.1.0

#### Added
- 9 core filesystem tools (fs_read_file, fs_write_file, fs_list_directory, fs_create_directory, fs_delete, fs_move, fs_copy, fs_search, fs_file_info)
- Agent loop with ReAct pattern (plan → execute → observe → reflect)
- Security sandbox with path validation and confirmation prompts
- Typer-based CLI with chat and ask modes
- Structured logging with Loguru
- JSONL audit trail for filesystem operations
- Pydantic v2 models for type-safe configuration
- Comprehensive test suite (target: >80% coverage)

#### Security
- Path traversal prevention
- ALLOWED_PATHS sandbox enforcement
- Confirmation prompts for destructive operations
- Audit logging for all modifications

## [0.1.0-alpha] - TBD

### Added
- Initial project scaffolding
- Interview-driven requirements (9 REQ documents)
- Architecture documentation (ARC-001, TECH-001)
- BassCodeBase integration (.bass-ready, CONTROL.yaml)
- Work breakdown structure (WBS-001 through WBS-015)

### Changed
- N/A (initial release)

### Deprecated
- N/A (initial release)

### Removed
- N/A (initial release)

### Fixed
- N/A (initial release)

### Security
- N/A (initial release)

---

## Version History

- **v0.1.0-alpha** - mai rilasciata
- **v0.1.0** - mai rilasciata (progetto chiuso il 2026-08-16)

---

## Migration Guides

### Upgrading to v0.1.0
- N/A (initial release)

---

## Notes

- This project follows [Semantic Versioning](https://semver.org/)
- For upgrade instructions, see the migration guides above
- For detailed changes, see the git commit history
