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

    for e_uuid in server.entities.keys():
        if server.entities[e_uuid]['is_alive']:
            logger.debug(f"update: {e_uuid=} {server.entities[e_uuid]['target']=}")
            logger.debug(f"update: Before {server.entities[e_uuid]['location']['x']=}")
            logger.debug(f"update: Before {server.entities[e_uuid]['location']['y']=}")
            logger.debug(f"update: Before {server.entities[e_uuid]['velocity']['x']=}")
            logger.debug(f"update: Before {server.entities[e_uuid]['velocity']['y']=}")
            server.entities[e_uuid]['location']['x'] += server.entities[e_uuid]['velocity']['x'] * dt
            server.entities[e_uuid]['location']['y'] += server.entities[e_uuid]['velocity']['y'] * dt
            # server.entities[e_uuid]['location']['x'] = 0 if server.entities[e_uuid]['location']['x'] < 0 else server.entities[e_uuid]['location']['x']
            # server.entities[e_uuid]['location']['x'] = 1280 - server.entities[e_uuid]['location']['width'] if server.entities[e_uuid]['location']['x'] > 1280 - server.entities[e_uuid]['location']['width'] else server.entities[e_uuid]['location']['x']
            # server.entities[e_uuid]['location']['y'] = 0 if server.entities[e_uuid]['location']['y'] < 0 else server.entities[e_uuid]['location']['y']
            # server.entities[e_uuid]['location']['y'] = 720 - server.entities[e_uuid]['location']['height'] if server.entities[e_uuid]['location']['y'] > 720 - server.entities[e_uuid]['location']['height'] else server.entities[e_uuid]['location']['y']
            logger.debug(f"update: After {server.entities[e_uuid]['location']['x']=}")
            logger.debug(f"update: After {server.entities[e_uuid]['location']['y']=}")
            logger.debug('-----')

            # # check distance to other entities
            # for other_uuid in [key for key in server.entities.keys() if server.entities[key]['is_alive'] and not e_uuid]:
            #     if other_uuid != e_uuid:
            #         # Calculate distance between entities
            #         dx = server.entities[e_uuid]['location']['x'] - server.entities[other_uuid]['location']['x']
            #         dy = server.entities[e_uuid]['location']['y'] - server.entities[other_uuid]['location']['y']
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
            #                 server.entities[e_uuid]['location']['x'] += nx * overlap * 0.5  # Adjust position
            #                 server.entities[e_uuid]['location']['y'] += ny * overlap * 0.5

            #                 # Move the other entity in the opposite direction
            #                 server.entities[other_uuid]['location']['x'] -= nx * overlap * 0.5
            #                 server.entities[other_uuid]['location']['y'] -= ny * overlap * 0.5

if __name__ == '__main__':
    server = WebSocketServer()
    server.run(update_entities, host=args.listen, port=args.port)