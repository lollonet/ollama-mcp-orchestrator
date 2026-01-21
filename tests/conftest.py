"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path
from typing import Generator

from ollama_mcp.config import OrchestratorConfig


@pytest.fixture
def tmp_project_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Create temporary project directory for testing."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Create sample files
    (project_dir / "file1.txt").write_text("Sample content 1")
    (project_dir / "file2.py").write_text("print('hello')")
    (project_dir / "subdir").mkdir()
    (project_dir / "subdir" / "file3.txt").write_text("Nested content")

    yield project_dir

    # Cleanup handled by tmp_path fixture


@pytest.fixture
def test_config(tmp_path: Path) -> OrchestratorConfig:
    """Create test configuration with temporary paths."""
    return OrchestratorConfig(
        ollama_model="qwen2.5:32b",
        ollama_host="http://localhost:11434",
        max_iterations=5,
        allowed_paths=[tmp_path],
        log_level="DEBUG",
        audit_log_path=tmp_path / "audit.jsonl",
    )


@pytest.fixture
def mock_ollama_response():
    """Mock Ollama API response."""
    return {
        "message": {
            "role": "assistant",
            "content": '{"tool": "fs_read_file", "args": {"path": "test.txt"}}',
        }
    }
