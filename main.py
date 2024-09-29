# Example file showing a circle moving on screen
import pygame
from scene import Scene

# pygame setup
pygame.init()

# set the clock
clock = pygame.time.Clock()
running = True
dt = 0

# create the scene manager
scene = Scene()

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