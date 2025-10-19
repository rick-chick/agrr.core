"""Daemon client for sending requests."""
import socket
import json
import sys
from typing import List

from . import SOCKET_PATH


def send_to_daemon(args: List[str]) -> int:
    """
    Send command to daemon and return exit code.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code (0 for success)
    """
    # リクエスト作成
    request = {
        'args': args
    }
    
    # ソケット接続
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(300)  # 5分タイムアウト
    
    try:
        sock.connect(SOCKET_PATH)
        
        # リクエスト送信（改行で終端）
        request_data = json.dumps(request).encode('utf-8') + b'\n'
        sock.sendall(request_data)
        
        # レスポンス受信（サーバーがshutdownするまで受信）
        response_data = b''
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                # サーバーがshutdownした（送信完了）
                break
            response_data += chunk
        
        # レスポンスパース
        response = json.loads(response_data.decode('utf-8'))
        
        # 出力
        if response.get('stdout'):
            print(response['stdout'], end='')
        
        if response.get('stderr'):
            print(response['stderr'], end='', file=sys.stderr)
        
        return response.get('exit_code', 0)
        
    finally:
        sock.close()

