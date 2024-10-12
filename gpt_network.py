import asyncio
import websockets
import json
import logging

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

class WebSocketServer:
    def __init__(self):
        self.connected_clients = {}
        self.messages = asyncio.Queue()  # Use an asyncio.Queue for safe access
        self.running = True
        self.entities = []

    async def handler(self, websocket, path):
        # Wait for the initial message containing the UUID
        try:
            initial_message = await websocket.recv()
            data = json.loads(initial_message)
            client_id = data.get("uuid")

            if not client_id:
                logger.error("No UUID provided by client. Closing connection.")
                await websocket.close()
                return
            
            self.connected_clients[client_id] = websocket
            logger.info(f"Client connected: {client_id}")

            async for message in websocket:
                await self.handle_message(client_id, message)

        finally:
            if client_id in self.connected_clients:
                del self.connected_clients[client_id]
                client_idx = None
                for idx, client in enumerate(self.entities):
                    if client['uuid'] == client_id:
                        client_idx = idx
                if client_idx:
                    logger.info('Removing client from current entities list.')
                    self.entities.pop(client_idx)
                else:
                    logger.info('Client not found in entity list.')
                logger.info(f"Client disconnected: {client_id}")

    async def handle_message(self, client_id, message):
        logger.debug(f"Received message from {client_id}: {message}")
        
        data = json.loads(message)
        
        found = False
        for idx, entity in enumerate(self.entities):
            if data['uuid'] == entity['uuid']:
                self.entities[idx] = data
                found = True
        if not found:
            self.entities.append(data)
        
        # Create combined payload
        combined_payload = {
            "entities": self.entities
        }

        # Broadcast the combined message to all connected clients
        await self.broadcast(client_id, combined_payload)

    async def broadcast(self, sender_id, message):
        logger.debug(f'Broadcast Message: {message=}')
        for client_id, websocket in self.connected_clients.items():
            if client_id != sender_id:  # Don't send the message back to the sender
                try:
                    await websocket.send(json.dumps(message))
                    logger.debug(f"Sent message to {client_id}: {message}")
                except Exception as e:
                    logger.error(f"Error sending message to {client_id}: {e}")

    def run(self, host='localhost', port=8765):
        start_server = websockets.serve(self.handler, host, port)
        asyncio.get_event_loop().run_until_complete(start_server)
        logger.info(f"WebSocket server started on ws://{host}:{port}")

        # Handle shutdown
        loop = asyncio.get_event_loop()
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            logger.info("Shutting down server...")
            self.running = False
            loop.run_until_complete(self.shutdown())

    async def shutdown(self):
        # Close all connections gracefully
        logger.info("Closing all client connections...")
        for client_id, websocket in self.connected_clients.items():
            await websocket.close()
            logger.info(f"Closed connection for client: {client_id}")

if __name__ == "__main__":
    server = WebSocketServer()
    server.run()
