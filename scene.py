"""
Current state of the game
"""
import pygame as pg
from entity import Player, Entity, Enemy
from sprite_sheet import SpriteSet
from random import randint
import uuid
from network import WebSocketClient  
import json
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
class Scene:
    def __init__(self, debug: bool=False, url: str='localhost', port: int=6789) -> None:
        self._uuid = uuid.uuid4()
        logger.info(self._uuid)
        self._ws_client = WebSocketClient(f'ws://{url}:{port}')
        self._ws_client.set_message_handler(self.handle_message)
        self._ws_client.start()
        self._screen = pg.display.set_mode((1280, 720))
        self._entities = []
        self._DEBUG = debug
        if self._DEBUG:
            # create 5 random entities if we are in debug mode
            for _ in range(6):
                loc = pg.Vector2(randint(0,self._screen.get_width()),
                    randint(0, self._screen.get_height()))
                self._entities.append(Enemy(loc))
        self._sprite_list = SpriteSet({'player': 'assets/player.png'})
        self._player = Player(pg.Vector2(self._screen.get_width() / 2, self._screen.get_height() / 2),
                {'player': self._sprite_list.get_sprite('player')}, self._uuid)
        self._font = pg.font.SysFont('Ariel', 30)
        self._score = 0

    def update(self, dt: float) -> None:
        self._player.update(dt)
        payload = {'uuid':str(self._uuid), 'entities':[]}
        if self._ws_client:
            send_data = self._player.serialize()
            send_data['type'] = 'player'
            send_data['timestamp'] = pg.time.get_ticks()
            logger.debug(send_data)
            payload['entities'].append(send_data)
            # self._ws_client.send(send_data)
        
        if not self._ws_client.running:
            for entity in self._entities:
                entity.move_to(self._player.get_location())
                entity.update(dt)
                logger.debug(f"{entity.get_location()=}")
        else:
                enemy_update = []
                for entity in self._entities:
                    logger.debug(self._player.check_collides(entity))
                    if type(entity) == Enemy:
                        if self._player.check_collides(entity):
                            was_alive = self._player.is_alive
                            self._player.damage(entity._atack)
                            if not self._player.is_alive and self._player.is_alive != was_alive:
                                self._score = pg.time.get_ticks()
                        if entity._target == self._uuid:
                            entity.move_to(self._player.get_location())
                            entity.update(dt)
                            enemy_update.append(entity)
                for enemy in enemy_update:
                    payload['entities'].append(enemy.serialize())
        self._ws_client.send(payload)

    def check_if_player_alive(self):
        logger.info(f'check_if_player_alive: {self._player.is_alive=}')
        return self._player.is_alive

    def handle_message(self, message):
        # Handle received message from the server
        logger.debug(f'handle_message: Received message: {type(message)=} {message=}')
        logger.debug(f'handle_message: Received {len(message.encode("utf-8"))} bytes')
        data = json.loads(message)
        if 'entities' in data.keys():
            for remote_entity in data['entities']:
                remote_uuid = uuid.UUID(remote_entity['uuid'])
                if remote_uuid != self._uuid:
                    found = False
                    for entity in self._entities:
                        if remote_uuid == entity.uuid:
                            if remote_entity['type'] == 'player' or \
                                (remote_entity['type'] == 'enemy' and remote_entity['target'] != str(self._uuid)):
                                entity.net_update(remote_entity)
                            found = True
                    if not found:
                        if remote_entity['type'] == 'player':
                            new_entity = Entity.from_dict(remote_entity, self._sprite_list, remote_uuid)
                        elif remote_entity['type'] == 'enemy':
                            target = uuid.UUID(remote_entity['target']) if remote_entity['target'] else None
                            new_entity = Enemy.from_dict(remote_entity, self._sprite_list, remote_uuid, target)
                        self._entities.append(new_entity)
        elif 'remove' in data.keys():
            logger.info('handle_message:Received remove message')
            remove_idx = None
            for idx, entity in enumerate(self._entities):
                if entity.uuid == uuid.UUID(data['remove']):
                    remove_idx = idx 
                    logger.info(f'handle_message:Found {data["remove"]}')
                    break
            if remove_idx:
                self._entities.pop(remove_idx)
            else:
                logger.info(f'handle_message:Could not find {data["remove"]}')

    def quit(self):
        self._ws_client.stop()

    def draw(self):
        self._screen.fill("forestgreen")
        for entity in self._entities:
            if type(entity) == Enemy:
                entity.draw(self._screen)
            else:
                entity.draw(self._screen, (255,255,0,255))
        if self._player.is_alive:
            self._player.draw(self._screen)
            score = self._score if self._score else pg.time.get_ticks()
            text_surface = self._font.render(f'Score: {score}', False, (0, 0, 0))
            self._screen.blit(text_surface, (0,0))
        else:
            game_over = self._font.render(f'Game Over', True, (128, 0, 0))
            score_text = self._font.render(f'Score for this run: {self._score}',True, (0,0,0))
            retry_text = self._font.render(f'Press space to retry', True, (0,0,0))
            self._screen.blit(game_over, 
                                (self._screen.get_width()/2 - game_over.get_width()/2,
                                self._screen.get_height()/2 - game_over.get_height() - score_text.get_height()/2))
            self._screen.blit(score_text, 
                                (self._screen.get_width()/2 - score_text.get_width()/2,
                                self._screen.get_height()/2 - score_text.get_height()/2))
            self._screen.blit(retry_text, 
                                (self._screen.get_width()/2 - retry_text.get_width()/2,
                                self._screen.get_height()/2 + retry_text.get_height() + score_text.get_height()/2))