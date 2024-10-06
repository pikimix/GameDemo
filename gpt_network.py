import asyncio
import websockets
import json
from queue import Queue
from threading import Thread
import sys
from time import sleep
class Server:
    def __init__(self, data_queue: Queue, command_queue: Queue, host="0.0.0.0", port=6789) -> None:
        self._host = host
        self._port = port
        self._server = None
        self._stopping = False
        self._data_queue = data_queue
        self._command_queue = command_queue

    async def start(self):
        self._server = await websockets.serve(self.echo, self._host, self._port)
        print(f"Server started at ws://{self._host}:{self._port}")

        # Start a separate task for processing the queue
        asyncio.create_task(self.process_queue())

        try:
            while not self._stopping:
                while not self._command_queue.empty():
                    if self._command_queue.get() == "quit":
                        self._stopping = True
                await asyncio.sleep(0.1) # Allow other tasks to run
        except asyncio.CancelledError:
            pass  # Allow graceful shutdown

    async def echo(self, websocket, path):
        async for message in websocket:
            data = json.loads(message)
            print(f"SERVER Received: {data}")
            self._data_queue.put(data)
            await websocket.send(json.dumps(data))
            print(f"SERVER Sent: {data}")

    async def process_queue(self):
        try:
            while not self._stopping:
                while not self._data_queue.empty():
                    received_data = self._data_queue.get()
                    print(f"Main thread processed data: {received_data}")
                await asyncio.sleep(0.1)  # Prevent busy waiting
        except asyncio.CancelledError:
            pass  # Allow graceful shutdown
        
    async def stop(self):
        print("Stopping server...")
        self._stopping = True  # Signal to stop the main loop
        if self._server:  # Ensure server is not None
            await self._server.wait_closed()  # Wait until the server is closed
            print("Server stopped.")


class Client:
    def __init__(self, data_queue: Queue, url="localhost", port=6789):
        self._data_queue = data_queue
        self._url = url
        self._port = port

    async def send_dict(self, data={"key1": "value1", "key2": "value2"}):
        uri = f"ws://{self._url}:{self._port}"
        try:
            async with websockets.connect(uri, timeout=5) as websocket:
                await websocket.send(json.dumps(data))
                print(f"CLIENT Sent: {data}")
                response = await websocket.recv()
                print(f"CLIENT Received: {json.loads(response)}")
                self._data_queue.put(json.loads(response))  # Store the response in the queue
        except asyncio.TimeoutError:
            print("Connection timed out.")
        except Exception as e:
            print(f"Error in client send_dict: {e}")

async def client_thread(data_queue: Queue, send_queue: Queue, url: str="localhost", port: int=6789):
    client = Client(data_queue, url, port)
    looping = True
    while looping:
        while not send_queue.empty():
            payload = send_queue.get()
            if payload:
                if payload == "quit":
                    looping = False
                await client.send_dict(payload)
            else:
                await client.send_dict()
            # Process data received in the queue
            while not data_queue.empty():
                received_data = data_queue.get()
                print(f"Main thread processed data: {received_data}")

def server_thread(data_queue, command_queue):
    # try:
        server = Server(data_queue, command_queue)
        asyncio.run(server.start())
        while not data_queue.empty():
            received_data = data_queue.get()
            print(f"Main thread processed data: {received_data}")
    # except KeyboardInterrupt:
    #     print("Keyboard Interrupt")
    #     asyncio.run(server.stop())  # Gracefully stop the server on keyboard interrupt
    #     print("Asyncio run called on server.stop")

def thread_runner(func, *args):
    try:
        asyncio.run(func(*args))
    except Exception as e:
        print(e)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <server|client>")
        sys.exit(1)

    mode = sys.argv[1].lower()
    if mode == "server":
        data_queue = Queue()
        command_queue = Queue()
        try:
            server_thread = Thread(target=thread_runner, args=(server_thread, data_queue, command_queue))
            server_thread.daemon = True
            server_thread.start()
            while True:
                while not data_queue.empty():
                    received_data = data_queue.get()
                    print(f"Main thread processed data: {received_data}")

        except KeyboardInterrupt:
            print("Caught intterupt")
            command_queue.put("quit")
            server_thread.join() 
    elif mode == "client":
        data_queue = Queue()
        send_queue = Queue()
        client_thread = Thread(target=thread_runner, args=(client_thread, data_queue, send_queue))
        client_thread.start()
        send_queue.put(None)
        send_queue.put({"key": "value"})
        send_queue.put("quit")
        client_thread.join()  # Wait for the client thread to finish
    else:
        print("Invalid mode. Use 'server' or 'client'.")
        sys.exit(1)
    print("End of file.")