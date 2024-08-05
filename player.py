class Player:
    def __init__(self, location, sprite) -> None:
        self.location = location
        self.sprite = sprite

    def update(self, pygame, dt) -> None:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            self.location.y -= 300 * dt
        if keys[pygame.K_s]:
            self.location.y += 300 * dt
        if keys[pygame.K_a]:
            self.location.x -= 300 * dt
        if keys[pygame.K_d]:
            self.location.x += 300 * dt

    def draw(self, screen):
        screen.blit(self.sprite, self.location, None)