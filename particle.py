from __future__ import annotations # To make type hinting work when using classes within this file
import logging
import pygame as pg

from sprite_sheet import AnimatedSprite

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class Particle:
    def __init__(self, start_time:float, origin:pg.Vector2, direction:pg.Vector2, speed:int=600, lifetime:float=1000, type='particle') -> None:
        self._origin: pg.Vector2 = origin
        self._direction: pg.Vector2 = direction.normalize()
        self._speed: int = speed
        self._lifetime: float = lifetime
        self._start_time: float = start_time
        self._time_alive: float = 0
        self._sprite: AnimatedSprite = AnimatedSprite(None, origin, radius=5)
        self._type: str = type
        self.new: bool = True
        self.complete: bool = False

    @staticmethod
    def from_dict(particle:dict, current_tick:float) -> Particle:
        new_particle = Particle(
            particle['start_time'],
            pg.Vector2(particle['origin']['x'], particle['origin']['y']),
            pg.Vector2(particle['direction']['x'], particle['direction']['y']),
            particle['speed'],
            particle['lifetime'],
            particle['type']
        )
        # Chances are the particle was created before we received it
        # Move it to its current location
        logger.info(f'from_dict: {new_particle.get_rect()} before catch up')
        if current_tick != particle['start_time']:
            dt = current_tick - particle['start_time']
            logger.info(f'from_dict: {dt=}')
            new_particle.update(dt)
        logger.info(f'from_dict: {new_particle.get_rect()} after catch up')
        return new_particle
    
    def serialize(self):
        return {
            'start_time': self._start_time,
            'origin': {
                'x': self._origin.x,
                'y': self._origin.y
                },
            'direction': {
                'x': self._direction.x,
                'y': self._direction.y
                },
            'speed': self._speed,
            'lifetime': self._lifetime,
            'type': self._type
        }

    def get_rect(self):
        return self._sprite.rect

    def update(self, dt:float) -> None:
        self.new = False
        self._sprite.update(self._direction * self._speed * dt)
        self.check_lifetime(dt)

    def check_lifetime(self, dt:float) -> None:
        self._time_alive += (dt*1000)
        if self._time_alive >= self._lifetime:
            self.complete = True
            self.new = False
        logger.debug(f'{self._time_alive=} {self._lifetime=}')

    def draw(self, screen, color=(255,128,255,255)):
        self._sprite.draw(screen, color=color)