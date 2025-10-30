"""Daemon module for fast CLI execution via UNIX socket."""
import os
import sys
from typing import List

SOCKET_PATH = '/tmp/agrr.sock'

def try_delegate_to_daemon(args: List[str]) -> bool:
    """
    Try to delegate command to daemon.
    
    Returns:
        True if delegated to daemon, False otherwise
    """
    # デーモン管理コマンドの場合
    if args and args[0] == 'daemon':
        from .manager import DaemonManager
        manager = DaemonManager()
        manager.handle_command(args[1:])
        return True
    
    # ソケットがあればデーモンに転送
    if os.path.exists(SOCKET_PATH):
        try:
            from .client import send_to_daemon
            exit_code = send_to_daemon(args)
            sys.exit(exit_code)
        except Exception as e:
            # デーモンエラーの場合はエラーで終了
            print(f"❌ Daemon error: {e}", file=sys.stderr)
            print("Please restart daemon: agrr daemon restart", file=sys.stderr)
            sys.exit(1)
    
    # デーモンがなければエラー
    print("❌ Daemon is not running", file=sys.stderr)
    print("Please start daemon: agrr daemon start", file=sys.stderr)
    sys.exit(1)

__all__ = ['try_delegate_to_daemon', 'SOCKET_PATH']

