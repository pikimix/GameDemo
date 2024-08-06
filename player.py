from sprite_sheet import Sprite
class Player:
    def __init__(self, location, sprite) -> None:
        self.location = location
        self.sprite = Sprite(sprite)
        self.facing_left = False

    def update(self, pygame, dt) -> None:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            self.location.y -= 300 * dt
        if keys[pygame.K_s]:
            self.location.y += 300 * dt
        if keys[pygame.K_a]:
            self.facing_left = True
            self.location.x -= 300 * dt
        if keys[pygame.K_d]:
            self.facing_left = False
            self.location.x += 300 * dt
        self.sprite.update()

    def draw(self, screen):
        self.sprite.draw(screen, self.location, flip=self.facing_left)