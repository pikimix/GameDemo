from sprite_sheet import Sprite
import pygame as pg

class Entity:
    def __init__(self, location: pg.Vector2, sprite: pg.Surface=None) -> None:
        self._location = location
        self._sprite = None
        if sprite:
            self._sprite = Sprite(sprite)
        self._facing_left = False
        self._velocity = pg.Vector2(0,0)

    def update(self, dt: float):
        self._location += self._velocity * dt

    def draw(self, screen):
        if self._sprite:
            self._sprite.draw(screen, self._location, flip=self._facing_left)
        else:
            pg.draw.circle(screen, (255,0,0), self._location, 10, 10)

class Player(Entity):
    def __init__(self, location, sprite) -> None:
        super().__init__(location, sprite)

    def update(self, dt) -> None:
        keys = pg.key.get_pressed()
        if keys[pg.K_w]:
            self._velocity.y = -300
        elif keys[pg.K_s]:
            self._velocity.y = 300
        else:
            self._velocity.y = 0
        if keys[pg.K_a]:
            self._facing_left = True
            self._velocity.x = -300
        elif keys[pg.K_d]:
            self._facing_left = False
            self._velocity.x = 300
        else:
            self._velocity.x = 0

        self._sprite.update()
        super().update(dt)
    
    def draw(self, screen):
        super().draw(screen)