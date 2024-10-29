import asyncio
import websockets
import json
import logging
import uuid
from random import randint, choice

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class WebSocketServer:
    def __init__(self):
        self.connected_clients = {}
        self.messages = asyncio.Queue()  # Use an asyncio.Queue for safe access
        self.running = True
        self.entities = []
        # self.entities = [
        #     {
        #         'type': 'enemy',
        #         'uuid': str(uuid.uuid4()),
        #         'location': {
        #             'x': choice([randint(0, 128), randint(1152, 1280)]), 
        #             'y': choice([randint(0, 128), randint(592, 720)]),
        #             'width' : 20,
        #             'height' : 20
        #         },
        #         'velocity': {'x': 0, 'y': 0},
        #         'sprite': None,
        #         'facing_left': False,
        #         'target': None
        #     }
        # ]
        self.last_message_time = asyncio.get_event_loop().time()  # Track last message time
        self.update_interval = 0.01  # Update interval in seconds
        self.scores = {}

    async def send_update(self):
        await self.broadcast(None, {"entities": self.entities})

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
            # add New enemy targeting the new player
            # self.entities.append({
            #     'type': 'enemy',
            #     'uuid': str(uuid.uuid4()),
            #     'location': {
            #         'x': choice([randint(0, 128), randint(1152, 1280)]), 
            #         'y': choice([randint(0, 128), randint(592, 720)]),
            #         'width' : 20,
            #         'height' : 20
            #     },
            #     'velocity': {'x': 0, 'y': 0},
            #     'sprite': None,
            #     'facing_left': False,
            #     'target': client_id
            # })
            self.spawn_enemies(client_id, 1)

            # Broadcast the combined message to all connected clients
            await self.broadcast(None, {"entities": self.entities})

            async for message in websocket:
                await self.handle_message(client_id, message)

        finally:
            removals = self.remove_entity(client_id)
            await asyncio.sleep(0.1)

            await self.broadcast(None, {"remove": removals})

    async def handle_message(self, client_id, message):
        logger.debug(f"Received message from {client_id}: {message}")
        # Update the last message time
        self.last_message_time = asyncio.get_event_loop().time()
        data = json.loads(message)
        if isinstance(data, dict):
            if 'entities' in data.keys():
                combined_payload = {}
                for r_entity in data['entities']:
                    found = False
                    remove_enemy = None
                    spawn_enemy = None
                    for idx, entity in enumerate(self.entities):
                        if r_entity['uuid'] == str(entity['uuid']):
                            if r_entity['type'] == 'enemy':
                                self.entities[idx]['velocity'] = r_entity['velocity']
                                self.entities[idx]['is_alive'] = r_entity['is_alive']
                            else:
                                if r_entity['type'] == 'player':
                                    if not r_entity['is_alive'] and self.entities[idx]['is_alive']:
                                        remove_enemy = r_entity['uuid']
                                    elif r_entity['is_alive'] and not self.entities[idx]['is_alive']:
                                        logger.info('handle_message: Should be trying to spawn enemies')
                                        spawn_enemy = r_entity['uuid']
                                self.entities[idx] = r_entity
                            found = True
                    if not found:
                        logger.error(f'handle_message: pretty sure there should never be a missing entity, but this one was {r_entity}')
                        self.entities.append(r_entity)
                    logger.debug(f'handle_message: {remove_enemy=} {spawn_enemy=}')
                    if remove_enemy:
                        removals = self.remove_enemys_targeting(remove_enemy)
                        combined_payload['remove'] = removals
                    if spawn_enemy:
                        self.spawn_enemies(spawn_enemy, 1)

                combined_payload["entities"] = self.entities
                
                # logger.debug(f'handle_message: {combined_payload=}')
                # Broadcast the combined message to all connected clients
                # await self.broadcast(client_id, combined_payload)
                # await self.broadcast(None, combined_payload)
            if 'score' in data.keys():
                if data['uuid'] in self.scores.keys():
                    logger.info(self.scores[data['uuid']])
                    # for breakpoint in [1000, 2500, 5000, 10000]:
                    if (self.scores[data['uuid']]['current_score'] // 2500) < (data['score'] // 2500):
                        logger.info(f'handle_message: Score crossed breakpoint for {data["name"]}')
                        self.spawn_enemies(data['uuid'],1)
                    self.scores[data['uuid']]['current_score'] = data['score']
                    if data['score'] > self.scores[data['uuid']]['score']:
                        self.scores[data['uuid']] = {'name': data['name'], 'score': data['score'], 'current_score': data['score']}
                        logger.debug(f'Set score for {data["uuid"]} to {self.scores[data["uuid"]]}')
                else:
                    self.scores[data['uuid']] = {'name': data['name'], 'score': data['score'], 'current_score': data['score']}
                    logger.debug(f'Set score for {data["uuid"]} to {self.scores[data["uuid"]]}')
                await self.broadcast(None, {'scores':self.scores})

    async def broadcast(self, sender_id, message):
        logger.debug(f'Broadcast Message: {message=}')
        for client_id, websocket in self.connected_clients.items():
            if client_id != sender_id:  # Don't send the message back to the sender
                try:
                    await websocket.send(json.dumps(message))
                    logger.debug(f"Sent message to {client_id}: {message}")
                except Exception as e:
                    logger.error(f"Error sending message to {client_id}: {e}")

    def spawn_enemies(self, target: str, number_to_spawn: int):
        logger.debug(f'spawn_enemies: {target=} {number_to_spawn=}')
        self.entities += [{
                'type': 'enemy',
                'uuid': str(uuid.uuid4()),
                'location': {
                    'x': choice([randint(0, 128), randint(1152, 1280)]), 
                    'y': choice([randint(0, 128), randint(592, 720)]),
                    'width' : 20,
                    'height' : 20
                },
                'velocity': {'x': 0, 'y': 0},
                'sprite': None,
                'facing_left': False,
                'target': target,
                'is_alive': True
            } for _ in range(number_to_spawn)]

    def remove_entity(self, entity_id):
        logger.info(f'remove_entity: Received removal for {entity_id}')
        if entity_id in self.connected_clients:
            logger.info(f'remove_entity: Received disconnect from {entity_id}')
            logger.debug(f'remove_entity: Removing from connected clients')
            del self.connected_clients[entity_id]
        if entity_id in self.scores.keys():
            logger.debug(f'remove_entity: Removing from scores')
            del self.scores[entity_id]
        entity_idx = next((idx for idx, client in enumerate(self.entities) if client['uuid'] == entity_id), None)
        if entity_idx:
            logger.debug('remove_entity: Removing from current entities list.')
            self.entities.pop(entity_idx)
        removals = self.remove_enemys_targeting(entity_id)
        # append entity we have removed to list of enemys removed
        removals.append(entity_id)
        return removals

    def remove_enemys_targeting(self, entity_id:str):
        logger.debug(f'remove_enemys_targeting: Removing enemies targeting {entity_id}')
        enemy_targets = [idx for idx, entity in enumerate(self.entities) if entity['type'] == 'enemy' and entity['target'] == entity_id]
        removals = []
        for idx in sorted(enemy_targets, reverse=True):
            # remove from list and broadcast removal to remaining clients
            removals.append(self.entities.pop(idx)['uuid'])
        return removals
    
    def run(self, update_function=None, host='localhost', port=8765):
        start_server = websockets.serve(self.handler, host, port)
        asyncio.get_event_loop().run_until_complete(start_server)
        logger.info(f"WebSocket server started on ws://{host}:{port}")

        # Start the periodic update task
        if update_function:
            asyncio.get_event_loop().create_task(update_function(self))

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
