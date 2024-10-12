"""
Current state of the game
"""
import pygame as pg
from entity import Player, Entity
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
                self._entities.append(Entity(loc))

        self._player = Player(pg.Vector2(self._screen.get_width() / 2, self._screen.get_height() / 2),
                pg.image.load("assets/player.png").convert_alpha(), self._uuid)

    def update(self, dt: float) -> None:
        self._player.update(dt)
        if self._ws_client:
            send_data = self._player.serialize()
            send_data['timestamp'] = pg.time.get_ticks()
            logger.debug(send_data)
            self._ws_client.send(send_data)
        
        if not self._ws_client.running:
            for entity in self._entities:
                entity.move_to(self._player.get_location())
                entity.update(dt)
                logger.debug(f"{entity.get_location()=}")
    
    def handle_message(self, message):
        # Handle received message from the server
        logger.info(f'Received message: {type(message)=} {message=}')
        data = json.loads(message)
        if 'entities' in data.keys():
            self._entities = []
            for entity in data['entities']:
                e_uuid = uuid.UUID(entity['uuid'])
                if e_uuid != self._uuid:
                    loc = pg.Vector2(entity['location']['x'], entity['location']['y'])
                    new_entity = Entity(loc, None, e_uuid)
                    self._entities.append(new_entity)

    def quit(self):
        self._ws_client.stop()

    def draw(self):
        self._screen.fill("forestgreen")
        self._player.draw(self._screen)
        for entity in self._entities:
            entity.draw(self._screen)