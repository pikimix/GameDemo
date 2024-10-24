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
    def __init__(self, name:str, debug: bool=False, url: str='localhost', port: int=6789) -> None:
        self._uuid = uuid.uuid4()
        logger.info(self._uuid)
        self._ws_client = WebSocketClient(f'ws://{url}:{port}')
        self._ws_client.set_message_handler(self.handle_message)
        self._ws_client.start()
        self._screen = pg.display.set_mode((1280, 720))
        self._entities = []
        self._sprite_list = SpriteSet({'player': 'assets/player.png'})
        self._player = Player(pg.Vector2(self._screen.get_width() / 2, self._screen.get_height() / 2),
                {'player': self._sprite_list.get_sprite('player')}, self._uuid, name)
        self._font = pg.font.SysFont('Ariel', 30)
        self._score = 0
        self._leader_board = {}
        #{'90565d97-c0c2-411c-9626-ed19874c4110': {'name': 'player1', 'score': 2899}, 'd8016dfb-6a2b-40a6-b2bd-1f338f94e2ca': {'name': 'player2', 'score': 953}}
        self._last_start = 0
        self._name = name

    def update(self, dt: float) -> None:
        enemies = [e for e in self._entities if type(e) == Enemy]
        # update animation for remote players
        [e.update_animation() for e in self._entities if type(e) == Entity]
        payload = {'uuid':str(self._uuid), 'name': self._name, 'entities':{}}
        if not self._player.is_alive:
            keys = pg.key.get_pressed()
            if keys[pg.K_SPACE]:
                self._score = 0
                self._last_start = pg.time.get_ticks()
                self._player.respawn(pg.Vector2(self._screen.get_width() / 2, self._screen.get_height() / 2),
                {'player': self._sprite_list.get_sprite('player')})
        else:
            self._score = pg.time.get_ticks() - self._last_start
            payload['score'] = self._score
            self._player.update(dt, self._screen.get_rect())
        enemy_update = []
        for enemy in enemies:
            if enemy.is_alive:
                collides = enemy.check_collides(self._player)
                if collides:
                    was_alive = self._player.is_alive
                    self._player.damage(enemy._atack)
                    if not self._player.is_alive and was_alive:
                        self._score = pg.time.get_ticks() - self._last_start
                        payload['score'] = self._score
                if enemy.target == self._uuid:
                    enemy.move_to_avoiding(self._player.get_location(), enemies)
                    enemy_update.append(enemy)
        for enemy in enemy_update:
            for e_uuid, enemy_dict in enemy.serialize().items():
                payload['entities'][e_uuid] = enemy_dict
                logger.info(f"{enemy_dict=}")

        for p_uuid, send_data in self._player.serialize().items():
            logger.debug(f'update: {p_uuid=} {send_data=}')
            payload['entities'][p_uuid] = (send_data)
        
        if self._ws_client.running:
            self._ws_client.send(payload)

    def collision_detection(self, enemies, enemies_rect):
        collision_list = self._player.get_rect().collidelistall(enemies_rect)
        for idx, enemy in enumerate(enemies):
            if idx in collision_list and enemy.check_collides(self._player):
                self._player.damage(enemy._atack)
            if enemy._target == self._uuid:
                enemy.move_to_avoiding(self._player.get_location(), enemies_rect)

    def check_if_player_alive(self):
        logger.info(f'check_if_player_alive: {self._player.is_alive=}')
        return self._player.is_alive

    def handle_message(self, message):
        # Handle received message from the server
        logger.debug(f'handle_message: Received message: {type(message)=} {message=}')
        logger.debug(f'handle_message: Received {len(message.encode("utf-8"))} bytes')
        data = json.loads(message)
        try:
            if 'entities' in data.keys():
                for r_uuid_str, remote_entity in data['entities'].items():
                    remote_uuid = uuid.UUID(r_uuid_str)
                    if remote_uuid != self._uuid:
                        found = False
                        for entity in self._entities:
                            if remote_uuid == entity.uuid:
                                entity.net_update(remote_entity)
                                found = True
                        if not found:
                            if remote_entity['type'] == 'player':
                                new_entity = Entity.from_dict(remote_entity, self._sprite_list, remote_uuid)
                                self._entities.append(new_entity)
                            elif remote_entity['type'] == 'enemy':
                                target = uuid.UUID(remote_entity['target']) if remote_entity['target'] else None
                                new_entity = Enemy.from_dict(remote_entity, self._sprite_list, remote_uuid, target)
                                self._entities.append(new_entity)
        except Exception as e:
            logger.error(f'{e=}')
        if 'remove' in data.keys():
            logger.error('handle_message:Received remove message - This should no longer happen')
            # if isinstance(data['remove'], list):
            #     for r_uuid in data['remove']:
            #         remove_idx = next((idx for idx, entity in enumerate(self._entities) if entity.uuid == uuid.UUID(r_uuid)), None)
            #         if isinstance(remove_idx, int):
            #             logger.info(f'handle_message:Found {r_uuid}')
            #             self._entities.pop(remove_idx)
            #         else:
            #             logger.info(f'handle_message:Could not find {r_uuid}')
            #     if r_uuid in self._leader_board.keys():
            #         del self._leader_board[r_uuid]
            # else:
            #     logger.error(f'handle_message: Received incorrectly formatted removal message : {data=}')
        if 'scores' in data.keys():
            self._leader_board = data['scores']

    def quit(self):
        self._ws_client.stop()

    def draw(self):
        self._screen.fill("forestgreen")
        for entity in self._entities:
            if entity.is_alive:
                if type(entity) == Enemy:
                    entity.draw(self._screen)
                else:
                    entity.draw(self._screen, (255,255,0,255))
        self.draw_scoreboard()
        if self._player.is_alive:
            self._player.draw(self._screen)
            score = self._score if self._score else pg.time.get_ticks() - self._last_start
            text_surface = self._font.render(f'Current Score: {score}', True, (0, 0, 0))
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
            
    def draw_scoreboard(self):
        score_header = self._font.render(f'All Player Top Scores', True, [0,0,0])
        score_lines = [score_header]
        line_height = 0
        for p_uuid, board in self._leader_board.items():
            line = self._font.render(f'{board["name"]}: {board["score"]}', True, [0,0,0])
            line_height = line.get_height()
            score_lines.append(line)
        for idx, line in enumerate(score_lines):
            self._screen.blit(
                line,
                (0,line_height*(idx+3))
            )