from sprite_sheet import Sprite
import pygame as pg

class Entity:
    def __init__(self, location: pg.Vector2, sprite: pg.Surface=None, uuid=None) -> None:
        self._uuid = uuid
        self._location = location
        self._sprite = None
        if sprite:
            self._sprite = Sprite(sprite)
        self._facing_left = False
        self._velocity = pg.Vector2(0,0)

    def move_to(self, destination: pg.Vector2):
        if destination.x > self._location.x:
            self._velocity.x = 200
        elif destination.x < self._location.x:
            self._velocity.x = -200
        else:
            self._velocity.x = 0

        if destination.y > self._location.y:
            self._velocity.y = 200
        elif destination.y < self._location.y:
            self._velocity.y = -200
        else:
            self._velocity.y = 0

    def get_location(self):
        if self._sprite:
            x = self._location.x + (self._sprite.width / 2)
            y = self._location.y + (self._sprite.height / 2)
            return pg.Vector2(x, y)
        else:
            return self._location

    def update(self, dt: float):
        self._location += self._velocity * dt

    def serialize(self):
        return {
            'uuid': str(self._uuid),
            'location' : { 'x' : self._location.x, 'y': self._location.y},
            'velocity' : { 'x' : self._velocity.x, 'y': self._velocity.y},
            'sprite': None
        }
    def draw(self, screen):
        if self._sprite:
            self._sprite.draw(screen, self._location, flip=self._facing_left)
        else:
            pg.draw.circle(screen, (255,0,0), self._location, 10, 10)

class Player(Entity):
    def __init__(self, location, sprite, uuid) -> None:
        super().__init__(location, sprite, uuid)

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