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

class AnimatedSprite(pg.sprite.Sprite):
    def __init__(self, image: pg.Surface, location:pg.Vector2=None) -> None:
        self.image = None
        self._frame = None
        self.rect = None
        if image:
            self.image = image
            self._frame = pg.Rect(0,0,32,64)
            if location:
                self.rect = pg.Rect(location.x,location.y,self._frame.width, self._frame.height)
            else:
                self.rect = pg.Rect(0,0,self._frame.width, self._frame.height)
        else:
            self.image = pg.Surface((20, 20), pg.SRCALPHA)
            pg.draw.circle(self.image, (255,255,255,255), (10,10), radius=10, width=0)
            self.rect = pg.Rect(0,0,20, 20)

        self._frame_update = 1000/10
        self._last_frame = 0

    def update(self, velocity: pg.math.Vector2):
        self.update_animation()
        self.rect.move_ip(velocity.x, velocity.y)
        
    def update_animation(self):
        current_time = pg.time.get_ticks()
        if self._frame:
            if current_time > self._last_frame + self._frame_update:
                self._frame.x += self._frame.width
                if self._frame.x >= self.image.get_width():
                    self._frame.x = 0
                self._last_frame = current_time

    def get_mask(self, flip) -> pg.Mask:
        flipped = pg.transform.flip(self.image.copy(),True,False) if flip else self.image.copy()
        surface = pg.Surface((self.rect.width,self.rect.height), pg.SRCALPHA)
        surface.blit(flipped, (0,0), self._frame)
        return pg.mask.from_surface(surface)

    def draw(self, screen: pg.Surface, color:pg.Color|tuple=None, flip: bool=False):
        tinted = self.image.copy()
        if color:
            tinted.fill(color,None,pg.BLEND_RGBA_MIN)
        screen.blit(pg.transform.flip(tinted,True,False) if flip else tinted, self.rect, self._frame)
        # mask = self.get_mask(flip)
        # screen.blit(mask.to_surface(),location)