from sprite_sheet import Sprite, SpriteSet
import pygame as pg
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class Entity:
    def __init__(self, location: pg.Vector2, sprite: dict=None, uuid=None) -> None:
        self.uuid = uuid
        self._location = location
        self._sprite = None
        self._sprite_name = None
        if sprite:
            for k,v in sprite.items():
                self._sprite_name = k
                self._sprite = Sprite(v)
        self._facing_left = False
        self._velocity = pg.Vector2(0,0)

    @staticmethod
    def from_dict(entity: dict, sprite_list: SpriteSet, e_uuid):
        loc = pg.Vector2(entity['location']['x'], entity['location']['y'])
        sprite = None
        if entity['sprite']:
            sprite = { entity['sprite']: sprite_list.get_sprite(entity['sprite']) }
        new_entity = Entity(loc, sprite, e_uuid)
        new_entity._facing_left= entity['facing_left']
        new_entity._velocity = pg.Vector2(entity['velocity']['x'], entity['velocity']['y'])
        return new_entity

    def move_to(self, destination: pg.Vector2):
        if destination.x > self._location.x:
            self._velocity.x = 200
        elif destination.x < self._location.x:
            self._velocity.x = -200
        else:
            self._velocity.x = 0

        if destination.y > self._location.y:
            self._velocity.y = 200
        elif destination.y < self._location.y:
            self._velocity.y = -200
        else:
            self._velocity.y = 0

    def get_location(self):
        if self._sprite:
            x = self._location.x + (self._sprite.width / 2)
            y = self._location.y + (self._sprite.height / 2)
            return pg.Vector2(x, y)
        else:
            return self._location

    def update(self, dt: float):
        self._location += self._velocity * dt

    def net_update(self, remote_entity:dict):
        self._location.x = remote_entity['location']['x']
        self._location.y = remote_entity['location']['y']
        self._velocity.x = remote_entity['velocity']['x']
        self._velocity.y = remote_entity['velocity']['y']
        self._facing_left = remote_entity['facing_left']
        
    def serialize(self):
        return {
            'uuid': str(self.uuid),
            'location' : { 'x' : self._location.x, 'y': self._location.y},
            'velocity' : { 'x' : self._velocity.x, 'y': self._velocity.y},
            'sprite': self._sprite_name,
            'facing_left': self._facing_left
        }
    def draw(self, screen, color=(255,0,0,255)):
        if self._sprite:
            self._sprite.draw(screen, self._location, flip=self._facing_left, color=color)
        else:
            pg.draw.circle(screen, (255,0,0,255), self._location, 10, 10)

class Enemy(Entity):
    def __init__(self, location: pg.Vector2, sprite: dict = None, uuid=None, target_uuid=None) -> None:
        self._target = target_uuid
        super().__init__(location, sprite, uuid)
    
    @staticmethod
    def from_dict(enemy: dict, sprite_list: SpriteSet, e_uuid, target_uuid):
        loc = pg.Vector2(enemy['location']['x'], enemy['location']['y'])
        sprite = None
        if enemy['sprite']:
            sprite = { enemy['sprite']: sprite_list.get_sprite(enemy['sprite']) }
        new_enemy = Enemy(loc, sprite, e_uuid, target_uuid)
        new_enemy._facing_left= enemy['facing_left']
        new_enemy._velocity = pg.Vector2(enemy['velocity']['x'], enemy['velocity']['y'])
        return new_enemy
    
    def update(self, dt: float):
        return super().update(dt)
    
    def serialize(self):
        return {
            'uuid': str(self.uuid),
            'location' : { 'x' : self._location.x, 'y': self._location.y},
            'velocity' : { 'x' : self._velocity.x, 'y': self._velocity.y},
            'sprite': self._sprite_name,
            'facing_left': self._facing_left,
            'target' : str(self._target),
            'type' : 'enemy'
        }
    
    def net_update(self, remote_entity: dict):
        if self._target != remote_entity['target']:
            logger.error(f'net_update:{self._target} != {remote_entity["target"]}')
        self._target = remote_entity['target']
        return super().net_update(remote_entity)

    def update_target(self, target_uuid):
        self._target = target_uuid
    
    def move_to_target(self, player_position_list:list):
        for player in player_position_list:
            if player['uuid'] == self._target:
                super().move_to(player['position'])

class Player(Entity):
    def __init__(self, location, sprite, uuid) -> None:
        super().__init__(location, sprite, uuid)

    def update(self, dt) -> None:
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

        self._sprite.update()
        super().update(dt)
    
    def draw(self, screen):
        super().draw(screen, color=(0,0,128,255))