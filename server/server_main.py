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
        logger.debug(f"{(current_time - last_update_time)=} {server.update_interval}")
        if current_time - last_update_time > server.update_interval:
            dt = current_time - last_update_time
            logger.debug("Running update")
            last_update_time = current_time
            await server.send_update()
        await asyncio.sleep(0.01)  # Adjust sleep time as needed

if __name__ == '__main__':
    server = WebSocketServer()
    server.run(update_entities, host=args.listen, port=args.port)