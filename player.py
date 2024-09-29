from sprite_sheet import Sprite
import pygame as pg
class Player:
    def __init__(self, location, sprite) -> None:
        self.location = location
        self.sprite = Sprite(sprite)
        self.facing_left = False

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