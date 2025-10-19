"""Lightweight entry point for agrr CLI with daemon support."""
import sys

# Try daemon first (fast import)
from agrr_core.daemon import try_delegate_to_daemon

if try_delegate_to_daemon(sys.argv[1:] if len(sys.argv) > 1 else []):
    sys.exit(0)

# Fallback to direct CLI execution (slow import)
from agrr_core.cli import execute_cli_direct

execute_cli_direct(sys.argv[1:] if len(sys.argv) > 1 else [])

