"""Daemon process manager."""
import os
import sys
import subprocess
import signal
import time
from pathlib import Path

from . import SOCKET_PATH


PID_FILE = '/tmp/agrr.pid'


class DaemonManager:
    """Manage daemon lifecycle (start/stop/status/restart)."""
    
    def handle_command(self, args):
        """
        Handle daemon subcommand.
        
        Args:
            args: Subcommand arguments
        """
        if not args or args[0] in ['--help', '-h', 'help']:
            self._print_help()
            sys.exit(0)
        
        cmd = args[0]
        
        if cmd == 'start':
            self.start()
        elif cmd == 'stop':
            self.stop()
        elif cmd == 'status':
            self.status()
        elif cmd == 'restart':
            self.restart()
        elif cmd == '_server':
            # Internal command: start daemon server
            self._start_server()
        else:
            print(f"Unknown command: {cmd}")
            self._print_help()
            sys.exit(1)
    
    def _print_help(self):
        """Print help message."""
        print("""
agrr daemon - Daemon process manager for faster command execution

What is daemon mode?
  Daemon mode keeps agrr loaded in memory, making subsequent commands
  4.8x faster (2.4s → 0.5s startup time).

  Note: Daemon is optional. All commands work without daemon,
        just slower on startup.

Usage:
  agrr daemon <command>

Commands:
  start      Start daemon in background (one-time setup)
  stop       Stop daemon
  status     Check if daemon is running
  restart    Restart daemon (if configuration changed)

Workflow:
  1. Start daemon (optional, for better performance):
     $ agrr daemon start

  2. Use agrr commands normally (they auto-detect daemon):
     $ agrr weather --location 35.6762,139.6503 --days 7
     $ agrr crop --query "tomato"
     (These run 4.8x faster with daemon)

  3. Check daemon status anytime:
     $ agrr daemon status

  4. Stop daemon when done (optional):
     $ agrr daemon stop

Examples:
  # Enable fast mode
  agrr daemon start

  # Run commands (automatically use daemon if available)
  agrr weather --location 35.6762,139.6503 --days 7

  # Check status
  agrr daemon status

  # Disable fast mode
  agrr daemon stop
""")
    
    def start(self):
        """Start daemon in background."""
        # 既に起動しているか確認
        if self._is_running():
            print("✗ Daemon is already running")
            sys.exit(1)
        
        # バックグラウンドで起動
        executable = sys.executable
        
        # デーモンプロセスを起動（内部コマンド _server を使用）
        # PyInstallerバイナリでも動作するように、自分自身を実行
        process = subprocess.Popen(
            [executable, 'daemon', '_server'] if getattr(sys, 'frozen', False) 
            else [executable, '-m', 'agrr_core', 'daemon', '_server'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True  # デーモン化
        )
        
        # 起動を待つ（最大5秒）
        for _ in range(50):
            if os.path.exists(SOCKET_PATH):
                print(f"✓ Daemon started (PID: {process.pid})")
                print(f"✓ Socket: {SOCKET_PATH}")
                return
            time.sleep(0.1)
        
        print("✗ Daemon failed to start")
        sys.exit(1)
    
    def _start_server(self):
        """Start daemon server (internal command)."""
        from .server import AgrrDaemon
        daemon = AgrrDaemon()
        daemon.start(pid_file=PID_FILE)
    
    def stop(self):
        """Stop daemon."""
        if not self._is_running():
            print("✗ Daemon is not running")
            return
        
        # PIDファイルから読み込み
        if os.path.exists(PID_FILE):
            try:
                with open(PID_FILE) as f:
                    pid = int(f.read().strip())
                
                # SIGTERMを送信
                os.kill(pid, signal.SIGTERM)
                
                # 停止を待つ（最大5秒）
                for _ in range(50):
                    if not os.path.exists(SOCKET_PATH):
                        print("✓ Daemon stopped")
                        return
                    time.sleep(0.1)
                
                # まだ動いてる場合はSIGKILL
                try:
                    os.kill(pid, signal.SIGKILL)
                    print("✓ Daemon stopped (forced)")
                except ProcessLookupError:
                    print("✓ Daemon stopped")
                    
            except (ValueError, ProcessLookupError):
                print("✗ Daemon was not running (cleaning up)")
                self._cleanup()
        else:
            # PIDファイルがない場合はソケットを削除
            self._cleanup()
            print("✓ Cleaned up stale socket")
    
    def status(self):
        """Check daemon status."""
        if self._is_running():
            # PIDを取得
            if os.path.exists(PID_FILE):
                with open(PID_FILE) as f:
                    pid = f.read().strip()
                print(f"✓ Daemon is running (PID: {pid})")
            else:
                print("✓ Daemon is running")
        else:
            print("✗ Daemon is not running")
            sys.exit(1)
    
    def restart(self):
        """Restart daemon."""
        print("Restarting daemon...")
        self.stop()
        time.sleep(0.5)
        self.start()
    
    def _is_running(self) -> bool:
        """Check if daemon is running."""
        if not os.path.exists(SOCKET_PATH):
            return False
        
        # ソケットに接続できるか試す
        import socket
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.connect(SOCKET_PATH)
            sock.close()
            return True
        except (ConnectionRefusedError, FileNotFoundError):
            # ソケットファイルはあるが接続できない（死んでる）
            self._cleanup()
            return False
    
    def _cleanup(self):
        """Clean up stale files."""
        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)

