from sprite_sheet import Sprite
import pygame as pg

class Entity:
    def __init__(self, location: pg.Vector2, sprite: pg.Surface=None) -> None:
        self._location = location
        self._sprite = None
        if sprite:
            self._sprite = Sprite(sprite)
        self._facing_left = False

    def update(self):
        pass

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
            self._location.y -= 300 * dt
        if keys[pg.K_s]:
            self._location.y += 300 * dt
        if keys[pg.K_a]:
            self._facing_left = True
            self._location.x -= 300 * dt
        if keys[pg.K_d]:
            self._facing_left = False
            self._location.x += 300 * dt
        self._sprite.update()
    
    def draw(self, screen):
        super().draw(screen)