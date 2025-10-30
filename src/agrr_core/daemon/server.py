"""Daemon server implementation."""
import socket
import json
import os
import sys
import io
import signal
import time
from typing import Optional

from . import SOCKET_PATH
from ..framework.logging.agrr_logger import DaemonLogger
from ..framework.config.config_loader import get_config

class AgrrDaemon:
    """Daemon server for fast CLI execution."""
    
    def __init__(self):
        """Initialize daemon (imports all heavy modules at startup)."""
        # Load configuration
        self.config = get_config()
        
        # Initialize logger
        daemon_log_file = self.config.get("logging.daemon_log_file", "/tmp/agrr_daemon.log")
        self.logger = DaemonLogger(daemon_log_file)
        
        # 重いモジュールを事前インポート（起動時の2秒はここで消費）
        # これによりリクエスト処理時は高速化される
        self.logger.info("Starting daemon, loading modules...")
        
        # 事前に重いモジュールをすべてインポート
        try:
            # Basic modules
            from agrr_core.framework.agrr_core_container import WeatherCliContainer
            from agrr_core.adapter.gateways.crop_profile_file_gateway import CropProfileFileGateway
            from agrr_core.adapter.gateways.crop_profile_inmemory_gateway import CropProfileInMemoryGateway
            from agrr_core.adapter.gateways.crop_profile_llm_gateway import CropProfileLLMGateway
            from agrr_core.adapter.gateways.weather_file_gateway import WeatherFileGateway
            from agrr_core.adapter.gateways.field_file_gateway import FieldFileGateway
            from agrr_core.adapter.presenters.crop_profile_craft_presenter import CropProfileCraftPresenter
            from agrr_core.adapter.controllers.crop_cli_craft_controller import CropCliCraftController
            from agrr_core.framework.services.clients.llm_client import LLMClient
            from agrr_core.framework.services.io.file_service import FileService
            
            # Optimize-related modules (for allocation adjust performance)
            from agrr_core.adapter.controllers.allocation_adjust_cli_controller import AllocationAdjustCliController
            from agrr_core.adapter.gateways.allocation_result_file_gateway import AllocationResultFileGateway
            from agrr_core.adapter.gateways.move_instruction_file_gateway import MoveInstructionFileGateway
            from agrr_core.usecase.interactors.allocation_adjust_interactor import AllocationAdjustInteractor
            from agrr_core.usecase.interactors.growth_period_optimize_interactor import GrowthPeriodOptimizeInteractor
            from agrr_core.adapter.gateways.interaction_rule_file_gateway import InteractionRuleFileGateway
            
            self.logger.info("Modules loaded successfully")
        except Exception as e:
            self.logger.error(f"Error loading modules", error=str(e))
        
    def start(self, pid_file: Optional[str] = None):
        """
        Start daemon server.
        
        Args:
            pid_file: Path to PID file
        """
        # ソケット作成
        if os.path.exists(SOCKET_PATH):
            # 既存のソケットを削除
            try:
                os.remove(SOCKET_PATH)
            except OSError:
                pass
        
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        
        try:
            sock.bind(SOCKET_PATH)
            os.chmod(SOCKET_PATH, 0o666)  # 誰でもアクセス可能
            sock.listen(5)
            
            # PIDファイル作成
            if pid_file:
                with open(pid_file, 'w') as f:
                    f.write(str(os.getpid()))
            
            self.logger.daemon_started(os.getpid(), SOCKET_PATH)
            
            # シグナルハンドラー設定
            def signal_handler(signum, frame):
                self.logger.daemon_stopped(os.getpid())
                sock.close()
                if os.path.exists(SOCKET_PATH):
                    os.remove(SOCKET_PATH)
                if pid_file and os.path.exists(pid_file):
                    os.remove(pid_file)
                sys.exit(0)
            
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
            # リクエストループ
            while True:
                try:
                    conn, addr = sock.accept()
                    self.logger.request_received("unknown", str(addr))
                    start_time = time.time()
                    
                    try:
                        self._handle_request(conn)
                        duration = time.time() - start_time
                        self.logger.request_completed("unknown", duration, 0)
                    except Exception as e:
                        duration = time.time() - start_time
                        self.logger.request_failed("unknown", str(e), duration)
                        
                except Exception as e:
                    self.logger.error(f"Error in request loop", error=str(e))
                    
        finally:
            sock.close()
            if os.path.exists(SOCKET_PATH):
                os.remove(SOCKET_PATH)
            if pid_file and os.path.exists(pid_file):
                os.remove(pid_file)
    
    def _handle_request(self, conn):
        """Handle single request."""
        try:
            # リクエスト受信（改行まで）
            data = b''
            while True:
                chunk = conn.recv(1024)
                if not chunk:
                    break
                data += chunk
                if b'\n' in data:
                    break
            
            if not data:
                return
            
            request = json.loads(data.decode('utf-8'))
            args = request.get('args', [])
            
            # 標準出力/エラー出力をキャプチャ
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture
            
            exit_code = 0
            
            try:
                # 既存のCLI実行関数を呼び出し
                from agrr_core.cli import execute_cli_direct
                execute_cli_direct(args)
            except SystemExit as e:
                exit_code = e.code if e.code is not None else 0
            except Exception as e:
                # エラーの詳細を記録（原因特定のため）
                import traceback
                error_details = traceback.format_exc()
                print(f"Error: {e}", file=sys.stderr)
                # FileNotFoundError/OSErrorの場合は必ず詳細なトレースバックを出力（原因特定のため）
                if isinstance(e, (FileNotFoundError, OSError)) or isinstance(e, OSError):
                    print(f"Traceback:\n{error_details}", file=sys.stderr)
                # FileNotFoundErrorの場合はファイル名も出力
                if isinstance(e, FileNotFoundError):
                    print(f"Missing file: {getattr(e, 'filename', 'unknown')}", file=sys.stderr)
                exit_code = 1
            finally:
                # 出力を復元
                sys.stdout = old_stdout
                sys.stderr = old_stderr
            
            # レスポンス作成
            response = {
                'stdout': stdout_capture.getvalue(),
                'stderr': stderr_capture.getvalue(),
                'exit_code': exit_code
            }
            
            # レスポンス送信（改行で終端）
            response_data = json.dumps(response).encode('utf-8') + b'\n'
            conn.sendall(response_data)
            
            # 送信完了を明示的に伝える
            conn.shutdown(socket.SHUT_WR)
            
        except Exception as e:
            self.logger.error(f"Error in _handle_request", error=str(e))
        finally:
            conn.close()

def main():
    """Entry point for daemon server."""
    pid_file = '/tmp/agrr.pid'
    daemon = AgrrDaemon()
    daemon.start(pid_file=pid_file)

if __name__ == '__main__':
    main()

