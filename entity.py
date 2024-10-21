from __future__ import annotations # To make type hinting work when using classes within this file
from sprite_sheet import AnimatedSprite, SpriteSet
import pygame as pg
import logging
import uuid
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
        self._hp = 100
        self._atack = 10
        self.is_alive = True
        self._name = name
        self._font = pg.font.SysFont('Futura', 30)

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
        new_entity._velocity = pg.Vector2(entity['velocity']['x'], entity['velocity']['y'])
        return new_entity

    def respawn(self, location: pg.Vector2, sprite: dict=None, uuid=None) -> None:
        self.uuid = uuid
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
        self._hp = 100
        self._atack = 10
        self.is_alive = True

    def damage(self, damage: int) -> None:
        self._hp -= damage
        if self._hp <= 0:
            self.is_alive = False

    def move_to(self, destination: pg.Vector2) -> None:
        if destination.x > self.get_location().x:
            self._velocity.x = 200
        elif destination.x < self.get_location().x:
            self._velocity.x = -200
        else:
            self._velocity.x = 0

        if destination.y > self.get_location().y:
            self._velocity.y = 200
        elif destination.y < self.get_location().y:
            self._velocity.y = -200
        else:
            self._velocity.y = 0


    def update_position(self, offset: tuple):
        self._sprite.rect.move(offset)


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
        # logger.info(f'{offeset=}')
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

    def net_update(self, remote_entity:dict) -> None:
        left = remote_entity['location']['x']
        top = remote_entity['location']['y']
        self._sprite.rect.update(left, top, self._sprite.rect.width, self._sprite.rect.height)
        self._velocity.x = remote_entity['velocity']['x']
        self._velocity.y = remote_entity['velocity']['y']
        self._facing_left = remote_entity['facing_left']
        
    def serialize(self) -> dict:
        return {
            'uuid': str(self.uuid),
            'location' : { 'x' : self._sprite.rect.left, 'y': self._sprite.rect.top,
                            'height': self._sprite.rect.height, 'width': self._sprite.rect.width},
            'velocity' : { 'x' : self._velocity.x, 'y': self._velocity.y},
            'sprite': self._sprite_name,
            'facing_left': self._facing_left,
            'name' : self._name,
            'is_alive' : self.is_alive
        }
    def draw(self, screen, color=(255,0,0,255)) -> None:
        self._sprite.draw(screen, flip=self._facing_left, color=color)
        if self._name:
            name = self._font.render(self._name, True, (0, 0, 0))
            name_pos = self.get_location()
            name_pos.x -= name.get_width()/2
            name_pos.y += self._sprite.rect.height/2
            screen.blit(name, name_pos)

class Enemy(Entity):
    def __init__(self, location: pg.Vector2, sprite: dict = None, uuid=None, target_uuid=None, name:str=None) -> None:
        self._target = target_uuid
        super().__init__(location, sprite, uuid, name)
    
    @staticmethod
    def from_dict(enemy: dict, sprite_list: SpriteSet, e_uuid, target_uuid) -> Enemy:
        loc = pg.Vector2(enemy['location']['x'], enemy['location']['y'])
        sprite = None
        if enemy['sprite']:
            sprite = { enemy['sprite']: sprite_list.get_sprite(enemy['sprite']) }
        new_enemy = Enemy(loc, sprite, e_uuid, target_uuid)
        new_enemy._facing_left= enemy['facing_left']
        new_enemy._velocity = pg.Vector2(enemy['velocity']['x'], enemy['velocity']['y'])
        return new_enemy
    
    def update(self, dt: float) -> None:
        return super().update(dt)
    
    def serialize(self) -> dict:
        ret_val = super().serialize()
        ret_val['target'] = str(self._target)
        ret_val['type'] = 'enemy'
        return ret_val
    
    def net_update(self, remote_entity: dict) -> None:
        if self._target != uuid.UUID(remote_entity['target']):
            logger.error(f'net_update:{self._target=} != {remote_entity["target"]=}')
        # self._target = remote_entity['target']
        return super().net_update(remote_entity)

    def update_target(self, target_uuid) -> None:
        self._target = target_uuid
    
    def move_to_target(self, player_position_list:list) -> None:
        for player in player_position_list:
            if player['uuid'] == self._target:
                super().move_to(player['position'])

class Player(Entity):
    def __init__(self, location, sprite, uuid, name:str=None) -> None:
        self._color = (0,0,128,255)
        super().__init__(location, sprite, uuid, name)

    def update(self, dt, bounds:pg.Rect) -> None:
        keys = pg.key.get_pressed()
        if keys[pg.K_w]:
            self._velocity.y = -300
        elif keys[pg.K_s]:
            self._velocity.y = 300
        else:
            self._velocity.y = 0
        if keys[pg.K_a]:
            self._facing_left = True
            self._velocity.x = -300
        elif keys[pg.K_d]:
            self._facing_left = False
            self._velocity.x = 300
        else:
            self._velocity.x = 0

        # self._sprite.update(self._velocity)
        super().update(dt, bounds)
    
    def draw(self, screen) -> None:
        super().draw(screen, color=self._color)