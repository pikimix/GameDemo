from __future__ import annotations # To make type hinting work when using classes within this file
from sprite_sheet import AnimatedSprite, SpriteSet
import pygame as pg
from math import radians
from random import randint
import time
import logging
import uuid

from particle import Particle

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class Entity:
    def __init__(self, location: pg.Vector2, sprite: dict=None, uuid:uuid.UUID=None, name:str=None) -> None:
        self.uuid = uuid
        self._sprite = None
        self._sprite_name = None
        if sprite:
            for k,v in sprite.items():
                self._sprite_name = k
                self._sprite = AnimatedSprite(v,location=location)
        else:
            self._sprite = AnimatedSprite(None,location=location)
        self._facing_left = False
        self._velocity = pg.Vector2(0,0)
        self._innertia_vector = pg.Vector2(0,0)
        self._innertia_scaler = 0
        self._max_velocity = 400
        self._hp = 100
        self._max_hp = 100
        self.attack_power = 25
        self.is_alive = True
        self._name = name
        self._type = 'entity'
        self._font = pg.font.SysFont('Futura', 30)
        self._draw_hp = True

    @staticmethod
    def from_dict(entity: dict, sprite_list: SpriteSet, e_uuid: uuid.UUID) -> Entity:
        loc = pg.Vector2(entity['location']['x'], entity['location']['y'])
        sprite = None
        if entity['sprite']:
            sprite = { entity['sprite']: sprite_list.get_sprite(entity['sprite']) }
        name = None
        if 'name' in entity.keys():
            name = entity['name']
        new_entity = Entity(loc, sprite, e_uuid, name)
        new_entity._facing_left= entity['facing_left']
        new_entity.is_alive = entity['is_alive']
        new_entity._velocity = pg.Vector2(entity['velocity']['x'], entity['velocity']['y'])
        return new_entity

    def respawn(self, location: pg.Vector2, sprite: dict=None) -> None:
        self._sprite = None
        self._sprite_name = None
        if sprite:
            for k,v in sprite.items():
                self._sprite_name = k
                self._sprite = AnimatedSprite(v, location)
        else:
            self._sprite = AnimatedSprite(None, location)
        self._facing_left = False
        self._velocity = pg.Vector2(0,0)
        self._hp = self._max_hp
        self.is_alive = True

    def damage(self, damage: int, velocity: pg.Vector2=None) -> None:
        self._hp -= damage
        if self._hp <= 0:
            self._innertia_scaler = 0
            self.is_alive = False
        elif velocity:
            self._innertia_vector = velocity.normalize()
            scaler = velocity.length()
            self._innertia_scaler = randint(int(scaler*2), int(scaler*3))

    def move_to(self, destination: pg.Vector2) -> None:
        target_velocity = destination - self.get_location()
        if target_velocity.length() != 0:
            target_velocity = target_velocity.normalize() * self._max_velocity
        self._velocity = target_velocity

    def move_to_avoiding(self, destination: pg.Vector2, avoid_list: dict[str,Entity], dt:float) -> None:
        logger.debug(f'move_to_avoiding: Moving {self.uuid=} towards {destination=}')
        # Determine target velocity towards the player
        self.move_to(destination)
        target_velocity = pg.Vector2(0, 0)

        collide_list = self.get_rect().collidedictall(avoid_list, values=True)

        # Check for collision with other avoid_list
        for o_uuid, o_rect in collide_list:
            distance = self.get_location().distance_to(avoid_list[o_uuid].center)
            if distance: # if distance is 0, assume this is us and skip
                collision_radius = avoid_list[o_uuid].width

                if distance < collision_radius:

                    # Calculate a direction vector to avoid the other entity
                    direction = self.get_location() - avoid_list[o_uuid].center

                    # Move away from the other entity
                    target_velocity += direction * self._max_velocity # Adjust strength as needed

        # Set the final velocity, ensuring it’s capped or constrained as needed
        if target_velocity.length() != 0:
            target_velocity.normalize_ip()
        if self._velocity.length() != 0:
            self._velocity.normalize_ip()
        self._velocity += target_velocity
        self._velocity *= (self._max_velocity)
        logger.debug(f'Entity:move_to_avoiding: {self._velocity.length()}')
        self.update(dt)

    def check_collides(self, other_entity:Entity) -> tuple|None:
        mask = self.get_mask()
        other_mask = other_entity.get_mask()
        x_offset = other_entity.get_rect().left - self.get_rect().left
        y_offset = other_entity.get_rect().top - self.get_rect().top 
        offeset = None
        if mask.overlap(other_mask,(x_offset,y_offset)):
            offeset = (self.get_rect().centerx - other_entity.get_rect().centerx,
                    self.get_rect().centery - other_entity.get_rect().centery
            )
        return offeset

    def get_rect(self) -> pg.Rect:
        return self._sprite.rect

    def get_mask(self) -> pg.Mask:
        if self._sprite:
            return self._sprite.get_mask(flip=self._facing_left)
        else:
            surface = pg.Surface((20,20), pg.SRCALPHA)
            pg.draw.circle(surface, (255,0,0,255), (10,10), radius=10, width=0)
            return pg.mask.from_surface(surface)

    def get_location(self) -> pg.Vector2:
        return pg.Vector2(self._sprite.rect.centerx, self._sprite.rect.centery)

    def update(self, dt: float, bounds:pg.Rect=None) -> None:
        logger.debug(f'Entity:update: {self._type=}{self._velocity=}')
        if self._innertia_scaler>0:
            inertia = self._innertia_vector * self._innertia_scaler
            # inertia += self._velocity
            self._sprite.update(inertia * dt)
            self._innertia_scaler -= self._max_velocity * 8 * dt
            logger.debug(f'{self._innertia_scaler=}')
        else:
            self._sprite.update(self._velocity * dt)
        if bounds:
            if self._sprite.rect.left < bounds.left:
                self._sprite.rect.left = bounds.left
            elif self._sprite.rect.right > bounds.right:
                self._sprite.rect.right = bounds.right
            if self._sprite.rect.top < bounds.top:
                self._sprite.rect.top = bounds.top
            elif self._sprite.rect.bottom > bounds.bottom:
                self._sprite.rect.bottom = bounds.bottom

    def update_animation(self):
        self._sprite.update_animation()

    def net_update(self, remote_entity:dict) -> None:
        try:
            logger.debug(f'net_update: {remote_entity=}')
            left = remote_entity['location']['x']
            top = remote_entity['location']['y']
            self._sprite.rect.update(left, top, self._sprite.rect.width, self._sprite.rect.height)
            self._velocity.x = remote_entity['velocity']['x']
            self._velocity.y = remote_entity['velocity']['y']
            self._facing_left = remote_entity['facing_left']
            self.is_alive = remote_entity['is_alive']
            self._hp = remote_entity['hp']
        except Exception as e:
            logger.error(f'{e=} {remote_entity}')
        
    def serialize(self) -> dict:
        return {    
            'location' : { 'x' : self._sprite.rect.left, 'y': self._sprite.rect.top,
                            'height': self._sprite.rect.height, 'width': self._sprite.rect.width},
            'velocity' : { 'x' : self._velocity.x, 'y': self._velocity.y},
            'sprite': self._sprite_name,
            'facing_left': self._facing_left,
            'name' : self._name,
            'is_alive' : self.is_alive,
            'max_velocity': self._max_velocity,
            'hp' : self._hp,
            'max_hp' : self._max_hp
        }

    def draw_healthbar(self, screen: pg.surface):
        rect = pg.Rect(self.get_rect().left, self.get_rect().top -15,
                        self.get_rect().width, 5)
        bar = pg.Rect(self.get_rect().left, self.get_rect().top -15,
                        ((self._hp/self._max_hp) *self.get_rect().width), 5)
        pg.draw.rect(screen, (255,0,0,255),bar)
        pg.draw.rect(screen, (0,0,0,255),rect,1,1)

    def draw(self, screen, color=(255,0,0,255)) -> None:
        if self._draw_hp: self.draw_healthbar(screen)
        self._sprite.draw(screen, flip=self._facing_left, color=color)
        if self._name:
            name = self._font.render(self._name, True, (0, 0, 0))
            name_pos = self.get_location()
            name_pos.x -= name.get_width()/2
            name_pos.y += self._sprite.rect.height/2
            screen.blit(name, name_pos)

class Enemy(Entity):
    def __init__(self, location: pg.Vector2, sprite: dict = None, uuid=None, target_uuid=None, name:str=None) -> None:
        self.target = target_uuid
        super().__init__(location, sprite, uuid, name)
        self._type = 'enemy'
        self._max_velocity = randint(self._max_velocity/2, self._max_velocity)
        self._draw_hp = False

    @staticmethod
    def from_dict(enemy: dict, sprite_list: SpriteSet, e_uuid: uuid.UUID) -> Enemy:
        sprite = None
        loc = pg.Vector2(enemy['location']['x'], enemy['location']['y'])
        if enemy['sprite']:
            sprite = { enemy['sprite']: sprite_list.get_sprite(enemy['sprite']) }
        target = uuid.UUID(enemy['target']) if enemy['target'] else None
        new_enemy = Enemy(loc, sprite, e_uuid, target)
        new_enemy._facing_left= enemy['facing_left']
        new_enemy.is_alive = enemy['is_alive']
        new_enemy._velocity = pg.Vector2(enemy['velocity']['x'], enemy['velocity']['y'])
        return new_enemy

    def respawn(self, location: pg.Vector2, sprite: dict = None, target:uuid=None) -> None:
        super().respawn(location, sprite)
        if target:
            self.target = target

    def serialize(self) -> dict:
        ret_val = super().serialize()
        ret_val['target'] = str(self.target)
        ret_val['type'] = 'enemy'
        return ret_val

    def net_update(self, remote_entity: dict) -> None:
        super().net_update(remote_entity)
        self.target = None if remote_entity['target'] == None else uuid.UUID(remote_entity['target'])

    def move_to_target(self, player_position_list:list) -> None:
        for player in player_position_list:
            if player['uuid'] == self.target:
                super().move_to(player['position'])
class Player(Entity):
    def __init__(self, location, sprite, uuid, name:str=None) -> None:
        super().__init__(location, sprite, uuid, name)
        self._color = (0,0,128,255)
        self._max_velocity = 450
        self._type = 'player'
        self.attack_particles: dict[str,Particle] = {}
        self._last_attack = 0
        self._attack_timer = 0
        self._next_attack = 500

    def update(self, dt, bounds:pg.Rect) -> None:
        keys = pg.key.get_pressed()
        target_velocity = pg.Vector2(0, 0) 
        if keys[pg.K_w]:
            target_velocity.y += -1
        if keys[pg.K_s]:
            target_velocity.y += 1
        
        if keys[pg.K_a]:
            self._facing_left = True
            target_velocity.x += -1
        if keys[pg.K_d]:
            self._facing_left = False
            target_velocity.x += 1

        mouse = pg.mouse.get_pressed(num_buttons=3)
        if mouse[0] == True:
            mouse_pos = pg.mouse.get_pos()
            mouse_pos = pg.Vector2(mouse_pos[0], mouse_pos[1])
            self.move_to(mouse_pos)
        else:
            if target_velocity.length() != 0:
                self._velocity = target_velocity.normalize() * self._max_velocity
            else:
                self._velocity = target_velocity
        logger.debug(f'player:update: {self._velocity.length()}')
        super().update(dt, bounds)
        completes = [a for a in self.attack_particles if self.attack_particles[a].complete]
        for c in completes:
            del self.attack_particles[c]
        [self.attack_particles[a].update(dt) for a in self.attack_particles]

    def attack(self, closest_point:pg.Vector2, dt:float, ticks:float ):
        if self.is_alive:
            self._attack_timer += (dt*1000)
            if self._last_attack + self._attack_timer >= self._last_attack + self._next_attack:
                ptcl_uuid = str(uuid.uuid4())
                self.attack_particles[ptcl_uuid] = Particle(time.time(), self.get_location(), closest_point - self.get_location())
                self._last_attack = ticks
                self._attack_timer = 0

    def serialize(self) -> dict:
        ret_val = super().serialize()
        ret_val['type'] = 'player'
        return ret_val
    
    def draw(self, screen) -> None:
        for _, particle in self.attack_particles.items():
            if not particle.complete: particle.draw(screen)
        super().draw(screen, color=self._color)
