import json
import threading
import websocket
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class WebSocketClient:
    def __init__(self, uri):
        self.uri = uri
        self.ws = None
        self.running = False
        self.message_handler = None

    def on_message(self, ws, message):
        logger.debug(f'on_message:Received message: {type(message)=} {message=}')  # Log the raw message
        try:
            # data = json.loads(message)
            if self.message_handler:
                self.message_handler(message)
        except json.JSONDecodeError as e:
            logger.error(f'on_message:JSON decode error: {e}')
        except TypeError as e:
            logger.error(f'on_message:Type error: {e}')
        except Exception as e:
            logger.error(f'on_message:An unexpected error occurred: {e}')


    def on_error(self, ws, error):
        print("WebSocket Error:", error)

    def on_close(self, ws, close_status_code, close_msg):
        logger.info(f'on_close: {close_status_code=}')
        logger.info(f'on_close: {close_msg=}')
        self.running = False
        # Attempt to reconnect
        # self.reconnect()

    def on_open(self, ws):
        print("WebSocket connection opened")

    def start(self):
        self.running = True
        self.connect()

    def connect(self):
        self.ws = websocket.WebSocketApp(self.uri,
                                        on_message=self.on_message,
                                        on_error=self.on_error,
                                        on_close=self.on_close)
        threading.Thread(target=self.ws.run_forever).start()

    def reconnect(self):
        if not self.running:
            self.start()

    def stop(self):
        self.running = False
        self.ws.close()

    def send(self, data):
        if self.ws and self.running:
            try:
                message = json.dumps(data)
                self.ws.send(message)
            except websocket.WebSocketConnectionClosedException:
                print("WebSocket connection is closed. Attempting to reconnect...")
                self.reconnect()

    def set_message_handler(self, handler):
        self.message_handler = handler