# extensions.py
from flask_socketio import SocketIO

socketio = SocketIO(cors_allowed_origins="*")
#socketio = SocketIO(cors_allowed_origins="*", logger=True, engineio_logger=True) para ver los logs de los sockets