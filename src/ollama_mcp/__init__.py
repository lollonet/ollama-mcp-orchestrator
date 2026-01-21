"""Ollama-MCP Filesystem Orchestrator.

Production-grade Python orchestrator enabling local Ollama models
to safely access the filesystem through the Model Context Protocol (MCP).
"""

__version__ = "0.1.0"
__author__ = "Claudio"
__license__ = "MIT"

from ollama_mcp.config import OrchestratorConfig

__all__ = ["OrchestratorConfig", "__version__"]
