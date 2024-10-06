"""
Current state of the game
"""
import pygame as pg
from entity import Player, Entity
from random import randint
from threading import Thread
from queue import Queue
from gpt_network import Client, thread_runner, client_thread
import uuid

class Scene:
    def __init__(self, debug: bool=False, server: bool|str=False, port: int=6789) -> None:
        self._server = None
        self._data_queue = None
        self._send_queue = None
        self._uuid = None
        self._client_thread = None
        if type(server) == bool:
            self._server = server
        elif type(server) == str:
            self._data_queue = Queue()
            self._send_queue = Queue()
            self._uuid = uuid.uuid4()
            self._client_thread = Thread(target=thread_runner, 
                                    args=(client_thread, 
                                    self._data_queue,
                                    self._send_queue,
                                    server, port))
            self._client_thread.start()
        self._screen = pg.display.set_mode((1280, 720))
        self._entities = []
        self._DEBUG = debug
        # if self._DEBUG:
        #     # create 5 random entities if we are in debug mode
        #     for _ in range(6):
        #         loc = pg.Vector2(randint(0,self._screen.get_width()),
        #             randint(0, self._screen.get_height()))
        #         self._entities.append(Entity(loc))

        self._player = Player(pg.Vector2(self._screen.get_width() / 2, self._screen.get_height() / 2),
                pg.image.load("assets/player.png").convert_alpha(), self._uuid)

    def update(self, dt: float) -> None:
        self._player.update(dt)
        if self._client_thread:
            print(self._player.serialize())
            self._send_queue.put(self._player.serialize())
            current_state={'timestamp':0}
            while not self._data_queue.empty():
                data = self._data_queue.get()
                if type(data) == dict \
                    and 'timestamp' in data.keys():
                    if current_state['timestamp'] < data['timestamp']:
                        current_state = data
            if 'entities' in current_state.keys():
                self._entities = current_state['entities']
        for entity in self._entities:
            entity.move_to(self._player.get_location())
            entity.update(dt)
            if self._DEBUG:
                print(f"{entity.get_location()=}")
    
    def quit(self):
        self._send_queue.put("quit")
        self._client_thread.join()

    def draw(self):
        self._screen.fill("forestgreen")
        self._player.draw(self._screen)
        for entity in self._entities:
            entity.draw(self._screen)