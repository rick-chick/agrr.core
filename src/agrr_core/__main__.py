"""Entry point for agrr CLI - daemon required."""
import sys

# Daemon delegation only (no fallback)
from agrr_core.daemon import try_delegate_to_daemon

try_delegate_to_daemon(sys.argv[1:] if len(sys.argv) > 1 else [])


