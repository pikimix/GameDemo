import pygame as pg

class Sprite:
    def __init__(self, image: pg.Surface) -> None:
        self.image = image
        self.frame = pg.Rect(0,0,32,64)
        self.frame_update = 1000/10
        self.last_frame = 0

    def update(self):
        current_time = pg.time.get_ticks()
        if current_time > self.last_frame + self.frame_update:
            self.frame.x += self.frame.width
            if self.frame.x >= self.image.get_width():
                self.frame.x = 0
            self.last_frame = current_time

    def draw(self, screen: pg.Surface, location: pg.Vector2, color=(0,0,128,255), flip: bool=False):
        self.image.fill(color,self.frame,pg.BLEND_RGBA_MIN)
        screen.blit(pg.transform.flip(self.image,True,False) if flip else self.image, location, self.frame) 