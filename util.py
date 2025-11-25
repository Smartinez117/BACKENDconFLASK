# extensions.py
from flask_socketio import SocketIO

socketio = SocketIO(cors_allowed_origins="*", async_mode="eventlet",path="/socket.io")
#socketio = SocketIO(cors_allowed_origins="*", logger=True, engineio_logger=True) 