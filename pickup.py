import logging
import pygame as pg
from sprite_sheet import AnimatedSprite

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class Pickup:
    def __init__(self, location: pg.Vector2, sprite: dict) -> None:
        self._sprite = None
        self.type = None
        for k, v in sprite.items():
            self.type = k
            self._sprite = AnimatedSprite(v,location=location)
        self.collected = False

    def get_rect(self):
        return self._sprite.rect

    def serialize(self):
        return {
            'x': self._sprite.rect.x,
            'y': self._sprite.rect.y,
            'type': self.type,
            'complete': self.collected
        }

    def draw(self, screen: pg.surface, color=(0,255,0,255)) -> None:
        if not self.collected:
            if self.type == 'shield':
                color = (0,0,255,255)
            self._sprite.draw(screen, flip=False, color=color)
