import pygame as pg

class SpriteSet:
    def __init__(self, sprites:dict) -> None:
        self._sprites = {}
        for name, file in sprites.items():
            surface = pg.image.load(file).convert_alpha()
            self._sprites[name] = surface

    def get_sprite(self, name:str) -> pg.Surface:
        if name in self._sprites.keys():
            return self._sprites[name]
        else:
            return None

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

    def draw(self, screen: pg.Surface, location: pg.Vector2, color:pg.Color|tuple=None, flip: bool=False):
        tinted = self._image.copy()
        if color:
            tinted.fill(color,None,pg.BLEND_RGBA_MIN)
        screen.blit(pg.transform.flip(tinted,True,False) if flip else tinted, location, self._frame) 