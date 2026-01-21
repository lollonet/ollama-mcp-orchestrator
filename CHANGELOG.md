# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

- **v0.1.0-alpha** - TBD - Initial alpha release
- **v0.1.0** - TBD - First stable release

---

## Migration Guides

### Upgrading to v0.1.0
- N/A (initial release)

---

## Notes

- This project follows [Semantic Versioning](https://semver.org/)
- For upgrade instructions, see the migration guides above
- For detailed changes, see the git commit history
