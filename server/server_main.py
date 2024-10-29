from server import WebSocketServer
from random import randint, choice
import asyncio
import logging
import pygame as pg
import argparse

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument("-l", "--listen", help="Listen IP", required=False, default='localhost')
parser.add_argument("-p", "--port", help="Server port to connect to, or listen on as server", required=False, default=8765)
parser.add_argument("-d", "--debug", help="Run with debug flags", action='store_true')
args = parser.parse_args()

async def update_entities(server :WebSocketServer):
    last_update_time = 0
    while server.running:
        current_time = asyncio.get_event_loop().time()
        # if current_time - server.last_message_time > server.update_interval:
        if current_time - last_update_time > server.update_interval:
            dt = current_time - last_update_time
            logger.debug("Running update")
            update(server, dt)  # Call the update method
            # Optionally, broadcast the updated state if necessary
            # await server.broadcast(None, {"entities": server.entities})
            last_update_time = current_time
            await server.send_update()
        await asyncio.sleep(0.01)  # Adjust sleep time as needed

def update(server, dt:float):
    collision_radius = 20
    for entity in server.entities:
        if entity['type'] == 'enemy':
            logger.debug(f"update: Updating enemy {entity['location']['x']=}")
            logger.debug(f"update: Updating enemy {entity['location']['y']=}")
            entity['location']['x'] += (entity['velocity']['x'] * dt)
            entity['location']['y'] += (entity['velocity']['y'] * dt)
            logger.debug(f"update: Updating enemy {entity['location']['x']=}")
            logger.debug(f"update: Updating enemy {entity['location']['y']=}")
            logger.debug('-----')
            bounds = pg.Rect(
                entity['location']['x'],
                entity['location']['y'],
                entity['location']['width'],
                entity['location']['height']
            )
            # # check distance to other entities
            # for other_entity in server.entities:
            #     if other_entity != entity and other_entity['type'] == 'enemy':
            #         # Calculate distance between entities
            #         dx = entity['location']['x'] - other_entity['location']['x']
            #         dy = entity['location']['y'] - other_entity['location']['y']
            #         distance = (dx**2 + dy**2)**0.5  # Euclidean distance

            #         # If they are too close, adjust positions
            #         if distance < collision_radius:
            #             # Calculate the overlap
            #             overlap = collision_radius - distance

            #             # Normalize the direction vector
            #             if distance > 0:
            #                 nx = dx / distance
            #                 ny = dy / distance
                            
            #                 # Move this entity away from the other entity
            #                 entity['location']['x'] += nx * overlap * 0.5  # Adjust position
            #                 entity['location']['y'] += ny * overlap * 0.5

            #                 # Move the other entity in the opposite direction
            #                 other_entity['location']['x'] -= nx * overlap * 0.5
            #                 other_entity['location']['y'] -= ny * overlap * 0.5

        # new_x = entity['location']['x'] + entity['velocity']['x']
        # new_y = entity['location']['y'] + entity['velocity']['y']
        # new_x = 0 if new_x < 0 else new_x
        # new_x = 1280 if new_x > 1280 else new_x
        # new_y = 0 if new_y < 0 else new_y
        # new_y = 720 if new_y > 720 else new_y
        # entity['location']['x'] = new_x
        # entity['location']['y'] = new_y
        # logger.debug(f'Updating Entity position to ({new_x},{new_y})')
        # entity['velocity']['x'] = choice([-200, 0, 200])
        # entity['velocity']['y'] = choice([-200, 0, 200])

if __name__ == '__main__':
    server = WebSocketServer()
    server.run(update_entities, host=args.listen, port=args.port)