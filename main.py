import signal
import sys
import os
import argparse

import pygame
from scene import Scene

def signal_handler(sig, frame):
    pygame.quit()
    sys.exit(0)

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--server", help="Run the process as a headless server", action='store_true')
parser.add_argument("-d", "--debug", help="Run the process as a headless server", action='store_true')
args = parser.parse_args()

DEBUG = args.debug
server = args.server

if server:
    os.environ["SDL_VIDEODRIVER"] = "dummy"

signal.signal(signal.SIGINT, signal_handler)

# pygame setup
pygame.init()

# set the clock
clock = pygame.time.Clock()
running = True
dt = 0

# create the scene manager
scene = Scene(debug=DEBUG, server=server)
if server:
    print("Server starting, press ctrl+c to exit.")

while running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
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