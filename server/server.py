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
        self.entities = {}
        for _ in range(101):
            self.entities[str(uuid.uuid4())] = {
                    'type': 'enemy',
                    'location': {
                        'x': choice([randint(0, 128), randint(1152, 1280)]), 
                        'y': choice([randint(0, 128), randint(592, 720)]),
                        'width' : 20,
                        'height' : 20
                    },
                    'velocity': {'x': 0, 'y': 0},
                    'sprite': None,
                    'facing_left': False,
                    'target': None,
                    'is_alive': False,
                    'hp': 100,
                    'damage': 10
                }
        self.players = {}
        # {
        #     str(uuid.uuid4()):{
        #         'type': 'player',
        #         'location': {
        #             'x': choice([randint(0, 128), randint(1152, 1280)]), 
        #             'y': choice([randint(0, 128), randint(592, 720)]),
        #             'width' : 20,
        #             'height' : 20
        #         },
        #         'velocity': {'x': 0, 'y': 0},
        #         'sprite': None,
        #         'facing_left': False,
        #         'target': None,
        #         'hp' : 100,
        #         'is_alive': False
        #     }
        # }
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
                for r_uuid, remote_entity in data['entities'].items():
                    if r_uuid in self.entities.keys():
                        logger.debug(f'before:{self.entities[r_uuid]["velocity"]}')
                        self.entities[r_uuid]['velocity'] = remote_entity['velocity']
                        logger.debug(f'after: {self.entities[r_uuid]["velocity"]}')
                        logger.debug(f"{self.entities[r_uuid]['target']=} {self.entities[r_uuid]['location']=}")
                        self.entities[r_uuid]['is_alive'] = remote_entity['is_alive']
                    elif r_uuid in self.players.keys():
                        if not remote_entity['is_alive'] and self.players[r_uuid]['is_alive']:
                            self.remove_enemys_targeting(r_uuid)
                        elif remote_entity['is_alive'] and not self.players[r_uuid]['is_alive']:
                            self.spawn_enemies(r_uuid,1)
                        self.players[r_uuid] = remote_entity
                    else:
                        try:
                            if remote_entity['type'] == 'enemy':
                                self.entities[r_uuid] = remote_entity
                            elif remote_entity['type'] == 'player':
                                self.players[r_uuid] = remote_entity
                        except Exception as e:
                            logger.info(f'\n\n{r_uuid=} {remote_entity=}\n\n')

                combined_payload["entities"] = {**self.entities, **self.players}
                
                # logger.debug(f'handle_message: {combined_payload=}')
                # Broadcast the combined message to all connected clients
                # await self.broadcast(client_id, combined_payload)
                # await self.broadcast(None, combined_payload)
            if 'score' in data.keys():
                if data['uuid'] in self.scores.keys():
                    logger.debug(self.scores[data['uuid']])
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
        logger.info(f'spawn_enemies: {target=} {number_to_spawn=}')
        spawned = 0
        for e_uuid, entity in self.entities.items():
            if not entity['is_alive'] and spawned < number_to_spawn:
                logger.info(f'spawn_enemy: Spawning {e_uuid=} to target {target=}')
                entity['is_alive'] = True
                entity['target'] = target
                entity['location']['x'] = choice([randint(0, 128), randint(1152, 1280)])
                entity['location']['y'] = choice([randint(0, 128), randint(592, 720)])
                spawned += 1
        if not spawned:
            logger.error('spawn_enemys: No Enemies to Spawn')

    def remove_entity(self, entity_id):
        logger.info(f'remove_entity: Received removal for {entity_id}')
        if entity_id in self.connected_clients:
            logger.info(f'remove_entity: Received disconnect from {entity_id}')
            logger.debug(f'remove_entity: Removing from connected clients')
            del self.connected_clients[entity_id]
        if entity_id in self.scores.keys():
            logger.debug(f'remove_entity: Removing from scores')
            del self.scores[entity_id]
        if entity_id in self.entities.keys():
            self.entities[entity_id]['is_alive'] = False
        if entity_id in self.players.keys():
            self.players[entity_id]['is_alive'] = False
        self.remove_enemys_targeting(entity_id)


    def remove_enemys_targeting(self, entity_id:str):
        logger.debug(f'remove_enemys_targeting: Removing enemies targeting {entity_id}')
        for e_uuid, entity in self.entities.items():
            if entity['target'] == entity_id:
                logger.info(f'remove_enemys_targeting: killing {e_uuid=} which was targeting {entity_id=}')
                entity['is_alive'] = False
                entity['target'] = None
        
    
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
