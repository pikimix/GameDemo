from __future__ import annotations # To make type hinting work when using classes within this file
import pygame as pg

from sprite_sheet import AnimatedSprite

class Particle:
    def __init__(self, start_time:float, origin:pg.Vector2, direction:pg.Vector2, speed:int=600, lifetime:float=1000) -> None:
        self._origin = origin
        self._direction = direction
        self._speed = speed
        self._lifetime = lifetime
        self._start_time = start_time
        self._time_alive = 0
        self._sprite = AnimatedSprite(None, origin)
        self.new = True
        self.complete = False
    @staticmethod
    def from_dict(particle:dict, current_tick:float) -> Particle:
        new_particle = Particle(
            particle['start_time'],
            particle['origin'],
            particle['direction'],
            particle['speed'],
            particle['lifetime']
        )
        # Chances are the particle was created before we received it
        # Move it to its current location
        if current_tick != particle['start_time']:
            dt = current_tick - particle['start_time']
            new_particle._sprite.update(
                new_particle._direction * new_particle._speed * dt)
        new_particle.check_lifetime(dt)
        return new_particle

    def update(self, dt:float) -> None:
        self.new = False
        self._sprite.update(self._direction * self._speed * dt)
        self.check_lifetime(dt)

    def check_lifetime(self, dt:float) -> None:
        self._time_alive += dt
        if self._time_alive >= self._lifetime:
            self.complete = True
            self.new = False