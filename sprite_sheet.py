import pygame as pg

class Sprite:
    def __init__(self, image: pg.Surface) -> None:
        self._image = image
        self._frame = pg.Rect(0,0,32,64)
        self.width = self._frame.width
        self.height = self._frame.height
        self._frame_update = 1000/10
        self._last_frame = 0

    
    def update(self):
        current_time = pg.time.get_ticks()
        if current_time > self._last_frame + self._frame_update:
            self._frame.x += self._frame.width
            if self._frame.x >= self._image.get_width():
                self._frame.x = 0
            self._last_frame = current_time

    def draw(self, screen: pg.Surface, location: pg.Vector2, color=(0,0,128,255), flip: bool=False):
        self._image.fill(color,self._frame,pg.BLEND_RGBA_MIN)
        screen.blit(pg.transform.flip(self._image,True,False) if flip else self._image, location, self._frame) 