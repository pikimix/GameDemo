from server import WebSocketServer
from random import randint, choice
import asyncio
import logging

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def update_entities(server):
    while server.running:
        current_time = asyncio.get_event_loop().time()
        if current_time - server.last_message_time > server.update_interval:
            logger.debug("Running update due to inactivity.")
            update(server)  # Call the update method
            # Optionally, broadcast the updated state if necessary
            await server.broadcast(None, {"entities": server.entities})
        await asyncio.sleep(0.1)  # Adjust sleep time as needed

def update(server):
    for entity in server.entities:
        new_x = entity['location']['x'] + entity['velocity']['x']
        new_y = entity['location']['y'] + entity['velocity']['y']
        new_x = 0 if new_x < 0 else new_x
        new_x = 1280 if new_x > 1280 else new_x
        new_y = 0 if new_y < 0 else new_y
        new_y = 720 if new_y > 720 else new_y
        entity['location']['x'] = new_x
        entity['location']['y'] = new_y
        logger.debug(f'Updating Entity position to ({new_x},{new_y})')
        entity['velocity']['x'] = choice([-200, 0, 200])
        entity['velocity']['y'] = choice([-200, 0, 200])

if __name__ == '__main__':
    server = WebSocketServer()
    server.run(update_entities)