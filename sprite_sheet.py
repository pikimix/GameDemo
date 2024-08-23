from pygame import Rect, time, transform, BLEND_RGBA_MIN

class Sprite:
    def __init__(self, image) -> None:
        self.image = image
        self.frame = Rect(0,0,32,64)
        self.frame_update = 1000/10
        self.last_frame = 0

    def update(self):
        current_time = time.get_ticks()
        if current_time > self.last_frame + self.frame_update:
            self.frame.x += self.frame.width
            if self.frame.x >= self.image.get_width():
                self.frame.x = 0
            self.last_frame = current_time

    def draw(self, screen, location, color=(0,0,128,255), flip=False):
        self.image.fill(color,self.frame,BLEND_RGBA_MIN)
        screen.blit(transform.flip(self.image,True,False) if flip else self.image, location, self.frame) 