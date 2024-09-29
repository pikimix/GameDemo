"""
Current state of the game
"""
import pygame as pg
from entity import Player, Entity
from random import randint

DEBUG = True
class Scene:
    def __init__(self) -> None:
        self._server = None
        self._screen = pg.display.set_mode((1280, 720))
        self._entities = []
        if DEBUG:
            # create 5 random entities if we are in debug mode
            for _ in range(6):
                loc = pg.Vector2(randint(0,self._screen.get_width()),
                    randint(0, self._screen.get_height()))
                self._entities.append(Entity(loc))

        self._player = Player(pg.Vector2(self._screen.get_width() / 2, self._screen.get_height() / 2),
                pg.image.load("assets/player.png").convert_alpha())

    def update(self, dt: float) -> None:
        self._player.update(dt)
        for entity in self._entities:
            entity.move_to(self._player.get_location())
            entity.update(dt)
    
    def draw(self):
        self._screen.fill("forestgreen")
        self._player.draw(self._screen)
        for entity in self._entities:
            entity.draw(self._screen)