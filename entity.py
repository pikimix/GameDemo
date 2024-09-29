from sprite_sheet import Sprite
import pygame as pg

class Entity:
    def __init__(self, location: pg.Vector2, sprite: pg.Surface) -> None:
        self.location = location
        self.sprite = Sprite(sprite)
        self.facing_left = False

class Player(Entity):
    def __init__(self, location, sprite) -> None:
        super().__init__(location, sprite)

    def update(self, dt) -> None:
        keys = pg.key.get_pressed()
        if keys[pg.K_w]:
            self.location.y -= 300 * dt
        if keys[pg.K_s]:
            self.location.y += 300 * dt
        if keys[pg.K_a]:
            self.facing_left = True
            self.location.x -= 300 * dt
        if keys[pg.K_d]:
            self.facing_left = False
            self.location.x += 300 * dt
        self.sprite.update()

    def draw(self, screen):
        self.sprite.draw(screen, self.location, flip=self.facing_left)