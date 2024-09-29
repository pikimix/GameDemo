"""
Current state of the game
"""
import pygame as pg
from player import Player

class Scene:
    def __init__(self) -> None:
        self._entities = []
        self._server = None
        self._screen = pg.display.set_mode((1280, 720))
        self._player = Player(pg.Vector2(self._screen.get_width() / 2, self._screen.get_height() / 2),
                pg.image.load("assets/player.png").convert_alpha())

    def update(self, dt: float) -> None:
        self._player.update(dt)
        for entity in self._entities:
            entity.update()
    
    def draw(self):
        self._screen.fill("purple")
        self._player.draw(self._screen)
        for entity in self._entities:
            entity.draw()