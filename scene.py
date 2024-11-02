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
    def __init__(self, name:str, debug: bool=False, url: str='localhost', port: int=6789, p_uuid=None) -> None:
        self.uuid = uuid.UUID(p_uuid) if p_uuid else uuid.uuid4()
        logger.info(self.uuid)
        self._ws_client = WebSocketClient(f'ws://{url}:{port}')
        self._ws_client.set_message_handler(self.handle_message)
        self._ws_client.start()
        self._screen = pg.display.set_mode((1280, 720))
        self._other_players: dict[str, Player] = {}
        self._enemies: dict[str, Enemy] = {}
        self._sprite_list = SpriteSet({'player': 'assets/player.png'})
        self._player = Player(pg.Vector2(self._screen.get_width() / 2, self._screen.get_height() / 2),
                {'player': self._sprite_list.get_sprite('player')}, self.uuid, name)
        self._font = pg.font.SysFont('Ariel', 30)
        self._score = 0
        self._leader_board = {}
        #{'90565d97-c0c2-411c-9626-ed19874c4110': {'name': 'player1', 'score': 2899}, 'd8016dfb-6a2b-40a6-b2bd-1f338f94e2ca': {'name': 'player2', 'score': 953}}
        self._last_start = 0
        self._name = name

    def update(self, dt: float) -> None:
        ticks = pg.time.get_ticks()
        logger.debug(f'update: {dt=}')
        enemies = {e:self._enemies[e] for e in self._enemies if self._enemies[e].is_alive}
        enemies_rect = {e:self._enemies[e].get_rect() for e in enemies}

        # update animation for remote players
        [self._other_players[e].update_animation() for e in self._other_players ]

        payload = {'uuid':str(self.uuid), 'name': self._name, 'entities':{}, 'time': ticks }
        if not self._player.is_alive:
            keys = pg.key.get_pressed()
            if keys[pg.K_SPACE]:
                self._score = 0
                self._last_start = ticks
                self._player.respawn(pg.Vector2(self._screen.get_width() / 2, self._screen.get_height() / 2),
                {'player': self._sprite_list.get_sprite('player')})
        else:
            self._score = ticks - self._last_start
            payload['score'] = self._score
            self._player.update(dt, self._screen.get_rect())
        was_alive = self._player.is_alive
        if enemies_rect: 
            self.collision_detection(enemies, enemies_rect)
            [enemies[e].move_to_avoiding(self._player.get_location(), enemies_rect, dt) for e in enemies if enemies[e].target == self.uuid]
            # [enemies[e].move_to(self._player.get_location(), dt) for e in enemies if enemies[e].target == self.uuid]
            
        if not self._player.is_alive:
            for e in enemies: 
                if enemies[e].target == self.uuid: 
                    enemies[e].is_alive = False
                    enemies[e].target = None
            if was_alive:
                self._score = ticks - self._last_start
                payload['score'] = self._score

        payload['entities'] = {e: enemies[e].serialize() for e in enemies if enemies[e].target == self.uuid}
        # add player to payload
        payload['entities'][str(self._player.uuid)] = self._player.serialize()
        
        if self._ws_client.running:
            # logger.info(f'\n\n{json.dumps(payload)=}\n\n')
            self._ws_client.send(payload)
    def collision_detection(self, enemies:dict[str, Enemy], enemies_rect:dict[str, pg.Rect]):
        collision_list = self._player.get_rect().collidedictall(enemies_rect, values=True)
        collision_list = [k[0] for k in collision_list]
        for key in collision_list:
            if key in enemies and enemies[key].check_collides(self._player):
                self._player.damage(enemies[key]._atack, enemies[key].get_location())
                break

    def check_if_player_alive(self):
        logger.info(f'check_if_player_alive: {self._player.is_alive=}')
        return self._player.is_alive

    def update_other_players(self, r_uuid_text, entity):
        logger.debug(f'{r_uuid_text=} {entity["is_alive"]=}')
        try:
            if r_uuid_text in self._other_players:
                self._other_players[r_uuid_text].net_update(entity)
            else:
                self._other_players[r_uuid_text] = Entity.from_dict(entity, self._sprite_list, uuid.UUID(r_uuid_text))
        except Exception as e:
            logger.error(f'update_other_players:add:{e=} : {r_uuid_text=} {entity=}')
    def update_enemy(self, r_uuid_text, entity):
        r_uuid = uuid.UUID(r_uuid_text)
        try:
            if r_uuid_text in self._enemies:
                self._enemies[r_uuid_text].net_update(entity)
            else:
                enemy = Enemy.from_dict(entity, self._sprite_list, r_uuid)
                self._enemies[r_uuid_text] = enemy
        except Exception as e:
            logger.error(f'update_enemy:add:{e=} : {r_uuid_text=} {r_uuid=} {entity=}')

    def handle_message(self, message):
        # Handle received message from the server
        logger.debug(f'handle_message: Received message: {type(message)=} {message=}')
        logger.debug(f'handle_message: Received {len(message.encode("utf-8"))} bytes')
        data = json.loads(message)
        if 'entities' in data.keys():
            for r_uuid, remote_entity in data['entities'].items():
                if r_uuid != str(self.uuid):
                    if remote_entity['type'] == 'player': self.update_other_players(r_uuid, remote_entity)
                    elif remote_entity['type'] == 'enemy': self.update_enemy(r_uuid, remote_entity)
                    else: logger.error(f"could not process: {r_uuid=} {remote_entity=}")
        if 'remove' in data.keys():
            logger.error('handle_message:Received remove message - This should no longer happen')
        if 'scores' in data.keys():
            self._leader_board = data['scores']

    def quit(self):
        self._ws_client.stop()

    def draw(self):
        self._screen.fill("forestgreen")
        for enemy in self._enemies:
            if self._enemies[enemy].is_alive:
                self._enemies[enemy].draw(self._screen)
        for player in self._other_players:
            logger.debug(f"{player=} {self._other_players[player].is_alive=}")
            if self._other_players[player].is_alive:
                self._other_players[player].draw(self._screen, (255,255,0,255))
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
        line_height = score_header.get_height()
        for p_uuid, board in self._leader_board.items():
            line = self._font.render(f'{board["name"]}: {board["score"]}', True, [0,0,0])
            score_lines.append(line)
        for idx, line in enumerate(score_lines):
            self._screen.blit(
                line,
                (0,line_height*(idx+3))
            )