import math
import random
import json

WIDTH = 1920
HEIGHT = 1080
FRAMERATE = 60

with open("src/items.json", "r") as source:
    ITEMDATA = json.load(source)
    source.close()

with open("src/entities.json", "r") as source:
    ENTITYDATA = json.load(source)
    source.close()



class Arena:

    def __init__(self, save : str):
        self.path = save
        self.save : dict = json.load(open(self.path))

        self.player = Player(
            self,
            self.save.get("x", 0.0),
            self.save.get("y", 0.0),
            self.save.get("rx", 0),
            self.save.get("ry", 0),
            self.loadItem(self.save.get("item", None)),
        )
        self.camera = Camera(self.player)

        self.rooms = [
            self.loadRoom(room) for room in self.save.get("rooms", [])
        ]

        self.scale : int = 75

    def saveGame(self):
        with open(self.path, "w") as savefile:
            json.dump(self.getSave(), savefile)
            savefile.close()

    def getSave(self) -> dict:
        return {
            "x": self.player.x,
            "y": self.player.y,
            "rx": self.player.rx,
            "ry": self.player.ry,
            "item": self.saveItem(self.player.item),
            "rooms": [
                self.saveRoom(room) for room in self.rooms
            ]
        }

    def loadItem(self, itemData : dict | None):
        if not itemData: return
        item = Item(
            itemData.get("id")
        )
        return item

    def saveItem(self, item):
        if not isinstance(item, Item): return
        return {
            "id": item.id,
        }

    def loadRoom(self, roomData : dict):
        room = Room(
            self,
            roomData.get("rx"),
            roomData.get("ry"),
            roomData.get("w"),
            roomData.get("h"),
            [
                self.loadBlock(block) for block in roomData.get("blocks", [])
            ],
            [
                self.loadEntity(entity) for entity in roomData.get("entities", [])
            ], [],
        )
        return room

    def saveRoom(self, room):
        if not isinstance(room, Room): return
        return {
            "rx": room.rx,
            "ry": room.ry,
            "w": room.w,
            "h": room.h,
            "blocks": [
                self.saveBlock(block) for block in room.layout
            ],
            "entities": [
                self.saveEntity(entity) for entity in room.entities
            ],
        }

    def loadBlock(self, blockData : dict):
        block = Block(
            self,
            blockData.get("x"),
            blockData.get("y"),
            blockData.get("w"),
            blockData.get("h"),
        )
        return block

    def saveBlock(self, block):
        if not isinstance(block, Block): return
        return {
            "x": block.x,
            "y": block.y,
            "w": block.w,
            "h": block.h,
        }

    def loadEntity(self, entityData : dict):
        entity = Entity(
            self,
            entityData.get("id"),
            entityData.get("x"),
            entityData.get("y"),
            **entityData.get("meta", {}),
        )
        return entity

    def saveEntity(self, entity):
        if not isinstance(entity, Entity): return
        return {
            "id": entity.id,
            "x": entity.x,
            "y": entity.y,
            "meta": entity.meta,
        }


    def getRoom(self, rx : int, ry : int):
        for room in self.rooms:
            if (rx, ry) == (room.rx, room.ry):
                return room
        return None

    def tick(self):
        self.player.tick()
        self.player.getRoom().tick()
        self.camera.tick()



class Room:

    def __init__(
        self,
        arena : Arena,
        rx : int,
        ry : int,
        w : int,
        h : int,
        layout : list,
        entities : list,
        particles : list,
    ):
        self.arena = arena
        self.rx, self.ry = rx, ry
        self.w, self.h = w, h
        self.layout : list[Block] = layout
        self.entities : list[Entity] = entities
        self.particles : list[Particle] = particles

    def tick(self):
        for entity in self.entities:
            entity.tick()
        for particle in self.particles:
            particle.tick()
            if particle.destroy:
                self.particles.remove(particle)
                del particle



class Block:

    def __init__(
        self,
        arena : Arena,
        x : float,
        y : float,
        w : float,
        h : float,
    ):
        self.arena = arena
        self.x, self.y = x, y
        self.w, self.h = w, h

    def collides(self, object) -> tuple[bool, bool, bool, bool]:
        w, a, s, d = False, False, False, False
        if not isinstance(object, (Player, Entity)): return w, a, s, d
        # print(type(object)) #

        colX = (self.x - self.w / 2 < object.x + object.w / 2 and object.x - object.w / 2 < self.x + self.w / 2)
        colY = (self.y - self.h / 2 < object.y + object.h / 2 and object.y - object.h / 2 < self.y + self.h / 2)

        if colX and (object.y - object.h / 2 < self.y - self.h / 2 < object.y + object.h / 2):
            w = True
        if colX and (object.y - object.h / 2 < self.y + self.h / 2 < object.y + object.h / 2):
            s = True
        if colY and (object.x - object.w / 2 < self.x - self.w / 2 < object.x + object.w / 2):
            a = True
        if colY and (object.x - object.w / 2 < self.x + self.w / 2 < object.x + object.w / 2):
            d = True

        return w, a, s, d



class Player:

    def __init__(
        self,
        arena : Arena,
        x : float,
        y : float,
        rx : int,
        ry : int,
        item,
    ):
        self.arena = arena
        self.x, self.y = x, y
        self.rx, self.ry = rx, ry

        self.item : Item = item

        self.w : float = 0.75
        self.h : float = 0.75

        self.speed : float = 0.35

    def getRoom(self):
        return self.arena.getRoom(self.rx, self.ry)

    def moveX(self, dx : float):
        self.x += dx

    def moveY(self, dy : float):
        self.y += dy

    def tick(self):
        for block in self.getRoom().layout:
            w, a, s, d = block.collides(self)
            if w: self.y = block.y - block.h / 2 - self.h / 2
            if s: self.y = block.y + block.h / 2 + self.h / 2
            if a: self.x = block.x - block.w / 2 - self.w / 2
            if d: self.x = block.x + block.w / 2 + self.w / 2



class Camera:

    def __init__(self, player : Player):
        self.player = player
        self.x : float = 0.0
        self.y : float = 0.0

        self.shakeForce = 0.0
        self.shakeDuration = 0
        self.shakeTimer = 0

    def tick(self):
        self.x = self.player.x
        self.y = self.player.y

        if self.shakeTimer > 0:
            self.shakeTimer -= 1
            if self.shakeTimer == 0:
                self.shakeForce = 0.0

    def shake(self, force : float, duration : int):
        if force > self.shakeForce:
            self.shakeForce = force
        if duration > self.shakeDuration:
            self.shakeDuration = duration

    def get(self):
        return (
            self.x + self.shakeForce * random.randint(-25, 25) / 100,
            self.y + self.shakeForce * random.randint(-25, 25) / 100,
        )



class Particle:

    def __init__(
        self,
        _id : str,
        x : float,
        y : float,
        vx : float,
        vy : float,
        t : int,
        ax : float = 0.0,
        ay : float = 0.0,
    ):
        self.id = _id
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.ax, self.ay = ax, ay
        self.t = t
        self.timer : int = 0

        self.destroy : bool = False

    def tick(self):
        self.timer += 1
        self.x += self.vx
        self.y += self.vy
        self.vx += self.ax
        self.vy += self.ay
        if self.timer >= self.t:
            self.destroy = True



class Item:

    def __init__(self, _id : str):
        self.id = _id
        self._data = ITEMDATA.get(self.id, {})

        self.name : str = self._data.get("name", "???")
        self.delay : int = self._data.get("delay", 0)

        self.timer : int = 0

    def tick(self):
        if self.timer > 0:
            self.timer -= 1

    def apply(self, point : tuple[float, float]):
        if self.timer > 0: return
        self.timer = self.delay
        return getattr(self, f"apply_{self.id}", self.apply_null)(point)


    def apply_null(self, point : tuple[float, float]):
        return



class Entity:

    def __init__(self, arena, _id : str, x : float, y : float, **meta : int | float | str):
        self.arena : Arena = arena
        self.id = _id
        self.meta = meta
        self._data = ENTITYDATA.get(self.id, {})

        self.x, self.y = x, y
        self.w : float = self._data.get("w", 0.75)
        self.h : float = self._data.get("h", 0.75)

        self.name : str = self._data.get("name", "???")
        self.max_hp : int = self._data.get("max_hp", 0)
        self.hp = self.max_hp

        self.timer : int = 0

    def tick(self) -> None:
        f = getattr(self, f"tick_{self.id}", self.tick_null)()
        self.timer += 1
        for block in self.arena.player.getRoom().layout:
            w, a, s, d = block.collides(self)
            # print(w, a, s, d) #
            if w: self.y = block.y - block.h / 2 - self.h / 2
            if s: self.y = block.y + block.h / 2 + self.h / 2
            if a: self.x = block.x - block.w / 2 - self.w / 2
            if d: self.x = block.x + block.w / 2 + self.w / 2
        return f

    def damage(self, amount : int) -> int:
        return getattr(self, f"damage_{self.id}", self.damage_null)(amount)

    def animate(self) -> str:
        return getattr(self, f"animate_{self.id}", self.animate_null)()


    def tick_null(self):
        return

    def damage_null(self, amount : int) -> int:
        pre = self.hp
        self.hp -= amount
        if self.hp < 0: self.hp = 0
        return pre - self.hp

    def animate_null(self) -> str:
        return f"entity_{self.id}"


    def tick_spider(self):
        distance = math.sqrt(
            (self.x - self.arena.player.x) ** 2 + (self.y - self.arena.player.y) ** 2
        )
        angle = math.atan2(
            self.arena.player.y - self.y, self.arena.player.x - self.x,
        )

        if distance > 1:
            self.x += 0.05 * math.cos(angle)
            self.y += 0.05 * math.sin(angle)