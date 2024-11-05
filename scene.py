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
from random import choice
from particle import Particle
from pickup import Pickup
import time
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
class Scene:
    def __init__(self, name:str, debug: bool=False, url: str='localhost', port: int=6789, p_uuid=None) -> None:
        self.uuid = uuid.UUID(p_uuid) if p_uuid else uuid.uuid4()
        logger.info(self.uuid)
        self._ws_client: WebSocketClient = WebSocketClient(f'ws://{url}:{port}')
        self._ws_client.set_message_handler(self.handle_message)
        self._ws_client.start()
        self._screen: pg.Surface = pg.display.set_mode((1280, 720))
        self._other_players: dict[str, Player] = {}
        self._enemies: dict[str, Enemy] = {}
        self._particles: dict[str,Particle] ={}
        self._pick_ups: dict[str,Pickup] = {}
        self._last_pickup: float = 0
        self._sprite_list: SpriteSet = SpriteSet({
            'player-round': {
                'file':'assets/player-rounder.png',
                'width': 32,
                'height': 32,
                'frames': 4
                
            },
            'player': {
                'file':'assets/player.png',
                'width': 32,
                'height': 64,
                'frames': 4
            },
            'health': {
                'file':'assets/cross-outline.png',
                'width': 16,
                'height': 16,
                'frames': 1
            },
            'shield':{
                'file':'assets/shield-shaded.png',
                'width': 16,
                'height': 16,
                'frames': 1
            }
        })
        self._player: Player = Player(pg.Vector2(self._screen.get_width() / 2, self._screen.get_height() / 2),
                {'player-round': self._sprite_list.get_sprite('player-round')}, self.uuid, name)
        self._font: pg.font.Font = pg.font.SysFont('Ariel', 30)
        self._score: int = 0
        self._score_additional: int = 0
        self._leader_board: dict[str:dict[str:str|int]] = {}
        #{'90565d97-c0c2-411c-9626-ed19874c4110': {'name': 'player1', 'score': 2899}, 'd8016dfb-6a2b-40a6-b2bd-1f338f94e2ca': {'name': 'player2', 'score': 953}}
        self._last_start: int = 0
        self._name: str = name
        self._current_ticks: int = 0

    def update(self, dt: float) -> None:
        self._current_ticks = pg.time.get_ticks()
        payload = {'uuid':str(self.uuid), 'name': self._name, 'entities':{}, 'time': time.time()}
        logger.debug(f'update: {dt=}')
        enemies = {e:self._enemies[e] for e in self._enemies if self._enemies[e].is_alive}
        enemies_rect = {e:self._enemies[e].get_rect() for e in enemies}

        self.player_attack(enemies, dt)

        killed = {}
        attacks = self._player.attack_particles
        for ptcl_uuid, particle in attacks.items():
            collides = particle.get_rect().collidedict(enemies_rect, values=True)
            if collides:
                enemies[collides[0]].is_alive = False
                enemies[collides[0]].target = None
                self._score_additional += 100
                particle.complete = True
                logger.debug(f'{collides[0]=} {enemies[collides[0]].is_alive=}')
                if enemies[collides[0]].target != self.uuid:
                    killed[collides[0]] = self._current_ticks
        if killed:
            payload['killed'] = killed
        new_particles = {p:attacks[p].serialize() for p in attacks if attacks[p].new}
        if new_particles:
            payload['particles'] = new_particles

        if self._current_ticks - self._last_pickup >= 5000 and self._player.is_alive:
            self._last_pickup = self._current_ticks
            pickup_uuid = str(uuid.uuid4())
            pwrup = choice(['health', 'shield'])
            #right now only health is implements
            pwrup = 'health'
            self._pick_ups[pickup_uuid] = Pickup(pg.Vector2(randint(0,1264), randint(0,704)),
                                                {pwrup: self._sprite_list.get_sprite(pwrup)})
            payload['pickups'] = {pickup_uuid: self._pick_ups[pickup_uuid].serialize()}
        
        pickup_rect = {p:self._pick_ups[p].get_rect() for p in self._pick_ups}
        collected = self._player.get_rect().collidedictall(pickup_rect, values=True)
        if collected:
            collected = [k[0] for k in collected]
            for k in collected:
                self._pick_ups[k].collected = True
                if 'pickups' in payload: payload['pickups'][k] = self._pick_ups[k].serialize()
                else: payload['pickups'] = {k:self._pick_ups[k].serialize()}
                if self._pick_ups[k].type == 'health':
                    self._player.heal()
                elif self._pick_ups[k].type == 'shield':
                    pass
        
        # update animation for remote players
        [self._other_players[e].update_animation() for e in self._other_players ]
        [self._particles[p].update(dt) for p in self._particles]
        for p in [p for p in self._particles if self._particles[p].complete]:
            if self._particles[p].complete:
                del self._particles[p]

        if not self._player.is_alive:
            keys = pg.key.get_pressed()
            if keys[pg.K_SPACE]:
                self._score = 0
                self._last_pickup = self._current_ticks
                self._last_start = self._current_ticks
                self._player.respawn(pg.Vector2(self._screen.get_width() / 2, self._screen.get_height() / 2),
                {'player-round': self._sprite_list.get_sprite('player-round')})
        else:
            self._score = self._current_ticks - self._last_start
            payload['score'] = self._score + self._score_additional
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
                self._score = self._current_ticks - self._last_start
                payload['score'] = self._score + self._score_additional

        payload['entities'] = {e: enemies[e].serialize() for e in enemies if enemies[e].target == self.uuid}
        # add player to payload
        payload['entities'][str(self._player.uuid)] = self._player.serialize()
        
        if self._ws_client.running:
            # logger.info(f'\n\n{json.dumps(payload)=}\n\n')
            self._ws_client.send(payload)

    def player_attack(self, enemies, dt):
        closest = None
        if enemies:
            closest = min([e for e in enemies], \
                            key=lambda e: self._player.get_location().distance_to(enemies[e].get_location()))
        logger.debug(f'{closest=}')
        if closest:
            self._player.attack(enemies[closest].get_location(), dt, self._current_ticks)

    def collision_detection(self, enemies:dict[str, Enemy], enemies_rect:dict[str, pg.Rect]):
        collision_list = self._player.get_rect().collidedictall(enemies_rect, values=True)
        collision_list = [k[0] for k in collision_list]
        for key in collision_list:
            if key in enemies and enemies[key].check_collides(self._player):
                self._player.damage(enemies[key].attack_power, enemies[key]._velocity)
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
        if entity['is_alive']:
            r_uuid = uuid.UUID(r_uuid_text)
            try:
                if r_uuid_text in self._enemies:
                    if self._enemies[r_uuid_text].target == self.uuid:
                        self._enemies[r_uuid_text].is_alive = entity['is_alive']
                    else:
                        self._enemies[r_uuid_text].net_update(entity)
                else:
                    enemy = Enemy.from_dict(entity, self._sprite_list, r_uuid)
                    self._enemies[r_uuid_text] = enemy
            except Exception as e:
                logger.error(f'update_enemy:{e=} : {r_uuid_text=} {r_uuid=} {entity=}')

    def update_pickup(self, pickup:dict[str,dict[str,str]]):
        logger.info(f'update_pickup: {pickup=}')
        for k,v in pickup.items():
            self._pick_ups[k] = Pickup(pg.Vector2(v['x'],v['y']),
                                                {v['type']: self._sprite_list.get_sprite(v['type'])}
                                                )
    def spawn_enemy(self, r_uuid, entity):
        logger.debug(f'spawn_enemy: Respawning {r_uuid}')
        location = pg.Vector2(choice([randint(0, 128), randint(1152, 1280)]),\
                                    choice([randint(0, 128), randint(592, 720)]))
        if r_uuid in self._enemies:
            self._enemies[r_uuid].respawn(location, target=uuid.UUID(entity['target']))
        else:
            self._enemies[r_uuid] = Enemy.from_dict(entity, self._sprite_list, r_uuid)

    def handle_message(self, message):
        # Handle received message from the server
        logger.debug(f'handle_message: Received message: {type(message)=} {message=}')
        logger.debug(f'handle_message: Received {len(message.encode("utf-8"))} bytes')
        data:dict[str:dict[str,object]] = json.loads(message)
        if 'entities' in data.keys():
            for r_uuid, remote_entity in data['entities'].items():
                if r_uuid != str(self.uuid):
                    if remote_entity['type'] == 'player': self.update_other_players(r_uuid, remote_entity)
                    elif remote_entity['type'] == 'enemy': self.update_enemy(r_uuid, remote_entity)
                    else: logger.error(f"could not process: {r_uuid=} {remote_entity=}")
        if 'spawn' in data:
            for r_uuid, entity in data['spawn'].items():
                if entity['target'] == str(self.uuid):
                    self.spawn_enemy(r_uuid, entity)
        if 'killed' in data:
            for r_uuid, ToD in data['killed']:
                if r_uuid in self._enemies:
                    self._enemies[r_uuid].is_alive = False
                    self._enemies[r_uuid].target = None
        if 'particles' in data and 'offset' in data:
            offset = data['offset']
            logger.debug(f'{offset=}')
            for p_uuid, particle in data['particles'].items():
                particle['start_time'] -= offset
                logger.debug(f'handle_message: {particle["start_time"]=} {self._current_ticks=}')
                self._particles[p_uuid] = Particle.from_dict(particle, time.time())
            logger.debug(f'handle_message: {len(self._particles)}')

        # if 'pickups' in data:
        #     logger.info(f'handle_message: {data["pickups"]=}')
        #     self.update_pickup(data['pickups'])

        if 'remove' in data.keys():
            logger.error(f'handle_message:Received remove message: {data["remove"]}')
        if 'scores' in data.keys():
            self._leader_board = data['scores']

    def quit(self):
        self._ws_client.stop()

    def draw(self):
        self._screen.fill("forestgreen")
        for enemy in self._enemies:
            if self._enemies[enemy].is_alive:
                self._enemies[enemy].draw(self._screen)
        for _, particle in self._particles.items():
            particle.draw(self._screen, (41,45,41,255))
        for player in self._other_players:
            logger.debug(f"{player=} {self._other_players[player].is_alive=}")
            if self._other_players[player].is_alive:
                self._other_players[player].draw(self._screen, (255,255,0,255))
        for pickup in self._pick_ups:
            self._pick_ups[pickup].draw(self._screen)

        self.draw_scoreboard()
        if self._player.is_alive:
            self._player.draw(self._screen)
            score = self._score + self._score_additional
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