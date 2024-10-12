import signal
import sys
import os
import argparse

import pygame
from scene import Scene

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def signal_handler(sig, frame):
    scene.quit()
    pygame.quit()
    sys.exit(0)

parser = argparse.ArgumentParser()
parser.add_argument("-u", "--url", help="Server URL to connect to, or IP to listen on as server", required=False, default="localhost")
parser.add_argument("-p", "--port", help="Server port to connect to, or listen on as server", required=False, default=8765)
parser.add_argument("-d", "--debug", help="Run with debug flags", action='store_true')
args = parser.parse_args()

DEBUG = args.debug
url = args.url
port = args.port

# if server:
#     os.environ["SDL_VIDEODRIVER"] = "dummy"

signal.signal(signal.SIGINT, signal_handler)

# pygame setup
pygame.init()

# set the clock
clock = pygame.time.Clock()
running = True
dt = 0

# create the scene manager
scene = None
# if server:
#     scene = Scene(debug=DEBUG, server=server, port=port)
#     print("Server starting, press ctrl+c to exit.")
# else:
scene = Scene(debug=DEBUG, url=url, port=port)

while running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            scene.quit()
            running = False
    
    # update the current scene
    scene.update(dt)

    # draw current scene
    scene.draw()

    # flip() the display to put your work on screen
    pygame.display.flip()

    # limits FPS to 60
    # dt is delta time in seconds since last frame, used for framerate-
    # independent physics.
    dt = clock.tick(60) / 1000

pygame.quit()