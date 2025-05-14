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

with open("src/grandom.json", "r") as source:
    RANDOMDATA = json.load(source)
    source.close()



def rollGeneration(rolldata : list[dict]) -> str:
    pool = []
    for roll in rolldata:
        pool.extend([roll.get("id", "???")] * roll.get("rolls", 1))
    return random.choice(pool)



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

        self.frozen : int = 0
        self.transdir : int = 0
        self.transtimer : int = 0

        # self.interacted : bool = False #

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
        if not itemData or itemData.get("id") == None: return None
        item = Item(
            self,
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
            roomData.get("type"),
            roomData.get("entrances"),
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
            "type": room.type,
            "entrances": [room.ew, room.ea, room.es, room.ed],
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

    def flash(self, x : float, y : float, force : int = 12, duration : int = 30):
        self.player.getRoom().light.append(Light(x, y, force, duration))

    def newEntity(self, _id : str, x : float, y : float, **meta : int | float | str):
        entity = Entity(
            self, _id, x, y, **meta,
        )
        self.player.getRoom().entities.append(entity)
        return entity

    def newParticle(
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
        particle = Particle(_id, x, y, vx, vy, t, ax, ay)
        self.player.getRoom().particles.append(particle)
        return particle

    def freeze(self, duration : int):
        self.frozen += duration

    def countOpponents(self) -> int:
        count = 0
        for entity in self.player.getRoom().entities:
            if entity.opponent: count += 1
        return count

    def countEntity(self, _id : str) -> int:
        count = 0
        for entity in self.player.getRoom().entities:
            if entity.id == _id: count += 1
        return count

    def tick(self):

        if self.transtimer > 0:
            self.transtimer -= 1

            if self.transtimer == FRAMERATE // 4:

                match self.transdir:

                    case 3:
                        self.player.rx -= 1
                        self.newRoom(self.player.rx, self.player.ry)
                        self.player.x = self.player.getRoom().w / 2 - 1
                        self.player.y = 0

                    case 1:
                        self.player.rx += 1
                        self.newRoom(self.player.rx, self.player.ry)
                        self.player.x = -self.player.getRoom().w / 2 + 1
                        self.player.y = 1

                    case 0:
                        self.player.ry -= 1
                        self.newRoom(self.player.rx, self.player.ry)
                        self.player.x = 0
                        self.player.y = self.player.getRoom().h / 2 - 1

                    case 2:
                        self.player.ry += 1
                        self.newRoom(self.player.rx, self.player.ry)
                        self.player.x = 0
                        self.player.y = -self.player.getRoom().h / 2 + 1

                for entity in self.player.getRoom().entities:
                    if entity.temporary:
                        entity.destroy = True

                self.player.getRoom().light.clear()
                self.player.getRoom().particles.clear()

        if not self.player.getRoom():
            self.newRoom(self.player.rx, self.player.ry)

        if self.frozen:
            self.frozen -= 1
            self.camera.tick()
            return

        self.player.tick()

        if self.player.x - self.player.w / 2 < -self.player.getRoom().w / 2:
            if self.player.getRoom().ea:
                self.freeze(FRAMERATE // 2)
                self.transdir = 3
                self.transtimer = FRAMERATE // 2

        if self.player.x + self.player.w / 2 > self.player.getRoom().w / 2:
            if self.player.getRoom().ed:
                self.freeze(FRAMERATE // 2)
                self.transdir = 1
                self.transtimer = FRAMERATE // 2

        if self.player.y - self.player.h / 2 < -self.player.getRoom().h / 2:
            if self.player.getRoom().ew:
                self.freeze(FRAMERATE // 2)
                self.transdir = 0
                self.transtimer = FRAMERATE // 2

        if self.player.y + self.player.h / 2 > self.player.getRoom().h / 2:
            if self.player.getRoom().es:
                self.freeze(FRAMERATE // 2)
                self.transdir = 2
                self.transtimer = FRAMERATE // 2

        self.player.getRoom().tick()
        self.camera.tick()



    def newRoom(self, rx : int, ry : int):
        gen = self.generateRoom(rx, ry)
        self.rooms.append(gen)
        return

    def generateRoom(self, rx : int, ry : int):

        chance = random.randint(1, 100)

        if chance <= 55:
            room = self.generateRoomPassage(rx, ry)
        else:
            room = self.generateRoomDungeon(rx, ry)

        return room

    def generateRoomPassage(self, rx : int, ry : int):

        room = Room(
            self,
            rx, ry,
            20, 20,
            [], [], [],
            "passage",
        )

        room.layout.append(Block(self, -8, -8, 4, 4))
        room.layout.append(Block(self, 8, -8, 4, 4))
        room.layout.append(Block(self, -8, 8, 4, 4))
        room.layout.append(Block(self, 8, 8, 4, 4))

        # for dx in (-1, 1):
        #     for dy in (-1, 1):
        #         froom = self.getRoom(rx + dx, ry + dy)
        #         if not froom:

        find = self.getRoom(rx, ry - 1)
        if find:
            # print(f"ROOM {rx} {ry - 1} FOUND : room.ew = {find.es}") #
            room.ew = find.es
        else:
            if random.randint(1, 3) == 1:
                room.ew = False
            else:
                room.ew = True

        find = self.getRoom(rx - 1, ry)
        if find:
            room.ea = find.ed
        else:
            if random.randint(1, 3) == 1:
                room.ea = False
            else:
                room.ea = True

        find = self.getRoom(rx, ry + 1)
        if find:
            room.es = find.ew
        else:
            if random.randint(1, 3) == 1:
                room.es = False
            else:
                room.es = True

        find = self.getRoom(rx + 1, ry)
        if find:
            room.ed = find.ea
        else:
            if random.randint(1, 3) == 1:
                room.ed = False
            else:
                room.ed = True


        if room.ew:
            room.layout.append(Block(self, -4, -8, 4, 4))
            room.layout.append(Block(self, 4, -8, 4, 4))
        else:
            room.layout.append(Block(self, 0, -8, 12, 4))

        if room.es:
            room.layout.append(Block(self, -4, 8, 4, 4))
            room.layout.append(Block(self, 4, 8, 4, 4))
        else:
            room.layout.append(Block(self, 0, 8, 12, 4))

        if room.ea:
            room.layout.append(Block(self, -8, -4, 4, 4))
            room.layout.append(Block(self, -8, 4, 4, 4))
        else:
            room.layout.append(Block(self, -8, 0, 4, 12))

        if room.ed:
            room.layout.append(Block(self, 8, -4, 4, 4))
            room.layout.append(Block(self, 8, 4, 4, 4))
        else:
            room.layout.append(Block(self, 8, 0, 4, 12))


        if random.randint(1, 3) == 1:
            room.layout.append(Block(self, 0, 0, 3, 3))

        if random.randint(1, 2) == 1:
            items = random.randint(1, 3)
            for i in range(items):
                ix = random.randint(2, 5) * random.choice((1, -1))
                iy = random.randint(2, 5) * random.choice((1, -1))
                iid = rollGeneration(RANDOMDATA.get("loot").get("ground"))
                room.entities.append(Entity(
                    self, "item", ix, iy, item_id = iid,
                ))


        return room


    def generateRoomDungeon(self, rx : int, ry : int):

        room = Room(
            self,
            rx, ry,
            30, 30,
            [], [], [],
            "dungeon",
        )

        room.layout.append(Block(self, -13, -13, 4, 4))
        room.layout.append(Block(self, 13, -13, 4, 4))
        room.layout.append(Block(self, -13, 13, 4, 4))
        room.layout.append(Block(self, 13, 13, 4, 4))

        find = self.getRoom(rx, ry - 1)
        if find:
            # print(f"ROOM {rx} {ry - 1} FOUND : room.ew = {find.es}") #
            room.ew = find.es
        else:
            if random.randint(1, 3) == 1:
                room.ew = False
            else:
                room.ew = True

        find = self.getRoom(rx - 1, ry)
        if find:
            room.ea = find.ed
        else:
            if random.randint(1, 3) == 1:
                room.ea = False
            else:
                room.ea = True

        find = self.getRoom(rx, ry + 1)
        if find:
            room.es = find.ew
        else:
            if random.randint(1, 3) == 1:
                room.es = False
            else:
                room.es = True

        find = self.getRoom(rx + 1, ry)
        if find:
            room.ed = find.ea
        else:
            if random.randint(1, 3) == 1:
                room.ed = False
            else:
                room.ed = True


        if room.ew:
            room.layout.append(Block(self, -6, -13, 10, 4))
            room.layout.append(Block(self, 6, -13, 10, 4))
            room.entities.append(Entity(self, "barricade", -0.5, -room.h / 2))
            room.entities.append(Entity(self, "barricade", 0, -room.h / 2))
            room.entities.append(Entity(self, "barricade", 0.5, -room.h / 2))
        else:
            room.layout.append(Block(self, 0, -13, 22, 4))

        if room.es:
            room.layout.append(Block(self, -6, 13, 10, 4))
            room.layout.append(Block(self, 6, 13, 10, 4))
            room.entities.append(Entity(self, "barricade", -0.5, room.h / 2))
            room.entities.append(Entity(self, "barricade", 0, room.h / 2))
            room.entities.append(Entity(self, "barricade", 0.5, room.h / 2))
        else:
            room.layout.append(Block(self, 0, 13, 22, 4))

        if room.ea:
            room.layout.append(Block(self, -13, -6, 4, 10))
            room.layout.append(Block(self, -13, 6, 4, 10))
            room.entities.append(Entity(self, "barricade", -room.w / 2, -0.5))
            room.entities.append(Entity(self, "barricade", -room.w / 2, 0))
            room.entities.append(Entity(self, "barricade", -room.w / 2, 0.5))
        else:
            room.layout.append(Block(self, -13, 0, 4, 22))

        if room.ed:
            room.layout.append(Block(self, 13, -6, 4, 10))
            room.layout.append(Block(self, 13, 6, 4, 10))
            room.entities.append(Entity(self, "barricade", room.w / 2, -0.5))
            room.entities.append(Entity(self, "barricade", room.w / 2, 0))
            room.entities.append(Entity(self, "barricade", room.w / 2, 0.5))
        else:
            room.layout.append(Block(self, 13, 0, 4, 22))


        # for i in range(random.randint(2, 5)):
        #     bx = random.randint(-5, 5)
        #     by = random.randint(-5, 5)
        #     room.layout.append(Block(self, bx, by, 1, 1))

        room.layout.append(Block(self, -4, -4, 3, 3))
        room.layout.append(Block(self, 4, -4, 3, 3))
        room.layout.append(Block(self, -4, 4, 3, 3))
        room.layout.append(Block(self, 4, 4, 3, 3))


        for i in range(random.randint(5, 12)):
            if random.randint(1, 2) == 1:
                ex = random.randint(-5, 5)
                ey = random.randint(-2, 2)
            else:
                ex = random.randint(-2, 2)
                ey = random.randint(-5, 5)
            eid = rollGeneration(RANDOMDATA.get("spawns").get("dungeon"))
            room.entities.append(Entity(self, eid, ex, ey))


        room.entities.append(Entity(self, "dungeon_chest", 0, 0))


        return room



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
        _type : str = "DEBUG",
        entrances : tuple[bool, bool, bool, bool] = (False, False, False, False),
    ):
        self.arena = arena
        self.rx, self.ry = rx, ry
        self.w, self.h = w, h
        self.layout : list[Block] = layout
        self.entities : list[Entity] = entities
        self.particles : list[Particle] = particles
        self.light : list[Light] = []

        self.type : str = _type

        self.ew, self.ea, self.es, self.ed = entrances

    def tick(self):
        for entity in self.entities:
            entity.tick()
            if entity.destroy:
                if entity.destroyTimer == 0:
                    self.entities.remove(entity)
                    del entity
                    continue

            if entity.x - entity.w / 2 < -self.w / 2:
                entity.x = -self.w / 2 + entity.w / 2
            if entity.x + entity.w / 2 > self.w / 2:
                entity.x = self.w / 2 - entity.w / 2
            if entity.y - entity.h / 2 < -self.h / 2:
                entity.y = -self.h / 2 + entity.h / 2
            if entity.y + entity.h / 2 > self.h / 2:
                entity.y = self.h / 2 - entity.h / 2

        for light in self.light:
            light.tick()

        for particle in self.particles:
            particle.tick()
            if particle.destroy:
                self.particles.remove(particle)
                del particle



class Light:

    def __init__(
        self,
        x : float,
        y : float,
        lum : int,
        duration : int,
    ):
        self.x = x
        self.y = y
        self.maxlum = lum
        self.lum : float = self.maxlum
        self.duration = duration
        self.timer = 0

        self.destroy = False

    def tick(self):
        self.timer += 1
        self.lum -= self.maxlum / self.duration
        if self.timer == self.duration:
            self.destroy = True



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

        collidedX = False
        collidedY = False

        if colX and (object.y - object.h / 2 < self.y - self.h / 2 < object.y + object.h / 2) and not collidedY:
            collidedX = True
            w = True
        if colX and (object.y - object.h / 2 < self.y + self.h / 2 < object.y + object.h / 2) and not collidedY:
            collidedX = True
            s = True
        if colY and (object.x - object.w / 2 < self.x - self.w / 2 < object.x + object.w / 2) and not collidedX:
            collidedY = True
            a = True
        if colY and (object.x - object.w / 2 < self.x + self.w / 2 < object.x + object.w / 2) and not collidedX:
            collidedY = True
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

        self.item : Item | None = item

        self.w : float = 0.75
        self.h : float = 0.75

        self.speed : float = 0.15
        self.stun : int = 0

        self.kb : int = 0
        self.kbangle : int = 0
        self.kbforce : float = 0.0

        self.max_hp : int = 12
        self.hp : int = self.max_hp
        self.eliminated : bool = False

    def getRoom(self):
        return self.arena.getRoom(self.rx, self.ry)

    def moveX(self, dx : float):
        if self.stun > 0: return
        if self.arena.frozen > 0: return
        self.x += dx

    def moveY(self, dy : float):
        if self.stun > 0: return
        if self.arena.frozen > 0: return
        self.y += dy

    def knockback(self, force : float, angle : int, duration : int):
        self.kbforce = force
        self.kbangle = angle
        self.kb = duration

    def hitstun(self, duration : int):
        self.stun = duration

    def damage(self, amount : int) -> int:
        pre = self.hp
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.eliminated = True
        return pre - self.hp

    def tick(self):
        if self.item:
            self.item.tick()

        if self.kb > 0:
            self.x += self.kbforce * math.cos(self.kbangle / 180 * math.pi)
            self.y += self.kbforce * math.sin(self.kbangle / 180 * math.pi)
            self.kb -= 1

        if self.stun > 0:
            self.stun -= 1

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
        if duration > self.shakeTimer:
            self.shakeTimer = duration

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

    def __init__(self, arena : Arena, _id : str):
        self.arena = arena
        self.id = _id

        self.loadData()

    def loadData(self):
        self._data = ITEMDATA.get(self.id, {})

        self.name : str = self._data.get("name", "???")
        self.delay : int = self._data.get("delay", 0)
        self.type : int = self._data.get("type", "CONSUME")

        self.automatic : bool = self._data.get("auto", False)
        self.reload_time : int = self._data.get("reload_time", 0)
        self.max_ammo : int = self._data.get("max_ammo", 0)
        self.ammo : int = self.max_ammo

        self.reloads : int = 0

        self.timer : int = 0

        self.equip()

    def tick(self):
        if self.timer > 0:
            self.timer -= 1
        if self.reloads > 0:
            self.reloads -= 1
            if self.reloads == 0:
                self.ammo = self.max_ammo

        return getattr(self, f"tick_{self.id}", self.tick_null)()

    def tick_null(self):
        return

    def reload(self):
        if self.reloads > 0: return
        if self.ammo == self.max_ammo: return
        self.reloads = self.reload_time

    def apply(self, point : tuple[float, float]):
        if self.timer > 0: return
        if self.reloads > 0: return
        self.timer = self.delay

        if self.type == "CONSUME":
            self.arena.player.item = None
        elif self.type == "SHOOTER":
            if self.ammo == 0:
                self.reload()
                return
            self.ammo -= 1

        return getattr(self, f"apply_{self.id}", self.apply_null)(point)

    def equip(self):
        return getattr(self, f"equip_{self.id}", self.equip_null)()
    def equip_null(self):
        return

    def dapply(self, point : tuple[float, float]):
        if self.timer > 0: return
        if self.reloads > 0: return
        if not self.automatic: return
        self.timer = self.delay

        if self.type == "CONSUME":
            self.arena.player.item = None
        elif self.type == "SHOOTER":
            if self.automatic:
                if self.ammo == 0:
                    return
                self.ammo -= 1

        return getattr(self, f"dapply_{self.id}", self.dapply_null)(point)


    def apply_null(self, point : tuple[float, float]):
        return
    def dapply_null(self, point : tuple[float, float]):
        return

    def apply_shotgun(self, point : tuple[float, float]):
        angle = math.atan2(
            self.arena.player.y - point[1], self.arena.player.x - point[0],
        ) + math.pi
        shotX = self.arena.player.x + math.cos(angle)
        shotY = self.arena.player.y + math.sin(angle)

        self.arena.flash(shotX, shotY, 120, FRAMERATE // 4)
        self.arena.player.knockback(0.15, (angle + math.pi) * 180 / math.pi, FRAMERATE // 8)
        self.arena.camera.shake(0.2, FRAMERATE // 8)
        self.arena.player.hitstun(FRAMERATE // 4)

        for e in range(-9, 9 + 1, 1):
            theta = angle + e / 180 * math.pi
            self.arena.newParticle(
                "powder",
                shotX, shotY,
                0.15 * math.cos(theta),
                0.15 * math.sin(theta),
                FRAMERATE // 4,
            )

        for i in range(-9, 9 + 1, 3):
            theta = angle + i / 180 * math.pi
            self.arena.newEntity(
                "bullet",
                self.arena.player.x + math.cos(theta),
                self.arena.player.y + math.sin(theta),
                angle = theta * 180 / math.pi,
                velocity = 0.45,
            )

        return


    def apply_machine_gun(self, point : tuple[float, float]):
        return self.dapply_machine_gun(point)

    def dapply_machine_gun(self, point : tuple[float, float]):
        angle = math.atan2(
            self.arena.player.y - point[1], self.arena.player.x - point[0],
        ) + math.pi
        shotX = self.arena.player.x + math.cos(angle)
        shotY = self.arena.player.y + math.sin(angle)

        self.arena.flash(shotX, shotY, 120, FRAMERATE // 4)
        self.arena.player.knockback(0.01, (angle + math.pi) * 180 / math.pi, FRAMERATE // 8)
        self.arena.camera.shake(0.05, FRAMERATE // 8)
        self.arena.player.hitstun(FRAMERATE // 8)

        inaccuracy = random.randint(-9, 9)

        self.arena.newEntity(
            "bullet",
            self.arena.player.x + math.cos(angle),
            self.arena.player.y + math.sin(angle),
            angle = angle * 180 / math.pi + inaccuracy,
            velocity = 0.45,
            duration = FRAMERATE,
        )

    def apply_grenade(self, point : tuple[float, float]):
        angle = math.atan2(
            self.arena.player.y - point[1], self.arena.player.x - point[0],
        ) + math.pi
        distance = math.sqrt(
            (self.arena.player.x - point[0]) ** 2 + (self.arena.player.y - point[1]) ** 2,
        )

        if distance > 3:
            selector = (
                self.arena.player.x + 3 * math.cos(angle),
                self.arena.player.y + 3 * math.sin(angle),
            )
        else:
            selector = point

        self.arena.newEntity("grenade", selector[0], selector[1])

    def apply_bandage(self, point : tuple[float, float]):
        self.arena.player.hp += 3
        if self.arena.player.hp > self.arena.player.max_hp:
            self.arena.player.hp = self.arena.player.max_hp

    def apply_turret(self, point : tuple[float, float]):
        self.arena.newEntity("turret", point[0], point[1])

    def apply_methane_can(self, point : tuple[float, float]):
        self.arena.newEntity("methane_can", point[0], point[1])


    def apply_rocket_launcher(self, point : tuple[float, float]):
        angle = math.atan2(
            self.arena.player.y - point[1], self.arena.player.x - point[0],
        ) + math.pi
        shotX = self.arena.player.x + math.cos(angle)
        shotY = self.arena.player.y + math.sin(angle)

        self.arena.flash(shotX, shotY, 120, FRAMERATE // 4)
        self.arena.player.knockback(0.35, (angle + math.pi) * 180 / math.pi, FRAMERATE // 8)
        self.arena.camera.shake(0.2, FRAMERATE // 8)
        self.arena.player.hitstun(FRAMERATE // 4)

        inaccuracy = random.randint(-2, 2)

        self.arena.newEntity(
            "rocket",
            self.arena.player.x + math.cos(angle),
            self.arena.player.y + math.sin(angle),
            angle = angle * 180 / math.pi + inaccuracy,
            velocity = 0.45,
            duration = FRAMERATE,
        )


    def equip_aura_blade(self):
        for e in range(9):
            angle = (360 // 9) * e
            self.arena.newEntity(
                "aura_wisp",
                self.arena.player.x + 1.75 * math.cos(angle / 180 * math.pi),
                self.arena.player.y + 1.75 * math.sin(angle / 180 * math.pi),
                angle = angle,
            )

    def tick_aura_blade(self):
        if self.arena.countEntity("aura_wisp") < 9:
            for e in range(9):
                angle = (360 // 9) * e
                self.arena.newEntity(
                    "aura_wisp",
                    self.arena.player.x + 1.75 * math.cos(angle / 180 * math.pi),
                    self.arena.player.y + 1.75 * math.sin(angle / 180 * math.pi),
                    angle = angle,
                )

    def apply_sword(self, point : tuple[float, float]):
        angle = math.atan2(
            self.arena.player.y - point[1], self.arena.player.x - point[0],
        ) * 180 / math.pi + 180
        self.arena.newEntity(
            "dagger",
            self.arena.player.x,
            self.arena.player.y,
            angle = angle,
            velocity = 0.45,
            duration = FRAMERATE // 8,
        )

    def apply_aura_blade(self, point : tuple[float, float]):
        angle = math.atan2(
            self.arena.player.y - point[1], self.arena.player.x - point[0],
        ) * 180 / math.pi + 180
        self.arena.newEntity(
            "dagger",
            self.arena.player.x,
            self.arena.player.y,
            angle = angle,
            velocity = 0.45,
            duration = FRAMERATE // 8,
        )


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
        self.ghostlike : bool = self._data.get("ghost", True)
        self.interactable : bool = self._data.get("interact", False)
        self.temporary : bool = self._data.get("temporary", False)
        self.opponent : bool = self._data.get("opponent", False)
        self.immune : bool = self._data.get("immune", False)

        self.kb : int = 0
        self.kbangle : int = 0
        self.kbforce : float = 0.0

        self.destroy = False
        self.destroyTimer : int = 0

        self.timer : int = 0

    def knockback(self, force : float, angle : int, duration : int):
        if self.immune: return
        self.kbforce = force
        self.kbangle = angle
        self.kb = duration

    def tick(self) -> None:
        if self.destroyTimer > 0:
            self.destroyTimer -= 1
            return
        f = getattr(self, f"tick_{self.id}", self.tick_null)()
        self.timer += 1

        if self.ghostlike:

            if self.kb > 0:
                self.x += self.kbforce * math.cos(self.kbangle / 180 * math.pi)
                self.y += self.kbforce * math.sin(self.kbangle / 180 * math.pi)
                self.kb -= 1

        for block in self.arena.player.getRoom().layout:
            w, a, s, d = block.collides(self)
            # print(w, a, s, d) #
            if w: self.y = block.y - block.h / 2 - self.h / 2
            if s: self.y = block.y + block.h / 2 + self.h / 2
            if a: self.x = block.x - block.w / 2 - self.w / 2
            if d: self.x = block.x + block.w / 2 + self.w / 2
        return f

    def damage(self, amount : int, angle : int = 90) -> int:
        if self.destroyTimer > 0: return
        if self.immune: return
        total = amount * 4
        damage = getattr(self, f"damage_{self.id}", self.damage_null)(amount)
        for i in range(round(angle - total // 2), round(angle + total // 2)):
            self.arena.newParticle(
                "heart",
                self.x, self.y,
                (0.15 + self.kbforce) * math.cos(i / 180 * math.pi),
                (0.15 + self.kbforce) * math.sin(i / 180 * math.pi),
                FRAMERATE // 8,
            )
        return damage

    def interact(self):
        if not self.interactable: return
        return getattr(self, f"interact_{self.id}", self.interact_null)()

    def animate(self) -> tuple[str, int]:
        # if self.ghostlike:
        #     if self.destroyTimer > 0:
        #         return f"knockout_{self.id}"
        return getattr(self, f"animate_{self.id}", self.animate_null)()


    def tick_null(self):
        return

    def damage_null(self, amount : int) -> int:
        if self.destroyTimer > 0: return
        pre = self.hp
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.destroy = True
            self.destroyTimer = FRAMERATE# // 2#
        return pre - self.hp

    def animate_null(self) -> tuple[str, int]:
        return f"entity_{self.id}", 0

    def interact_null(self):
        return


    def tick_spider(self):
        if not "cooldown" in self.meta.keys():
            self.meta["cooldown"] = 0

        distance = math.sqrt(
            (self.x - self.arena.player.x) ** 2 + (self.y - self.arena.player.y) ** 2
        )
        angle = math.atan2(
            self.arena.player.y - self.y, self.arena.player.x - self.x,
        )

        if 12 > distance > 1:
            self.x += 0.05 * math.cos(angle)
            self.y += 0.05 * math.sin(angle)

        if self.meta["cooldown"] > 0:
            self.meta["cooldown"] -= 1

        if distance < 4:
            if self.meta["cooldown"] == 0:
                self.arena.newEntity(
                    "web",
                    self.x, self.y,
                    angle = angle * 180 / math.pi,
                    velocity = 0.15,
                )
                self.meta["cooldown"] = FRAMERATE * 2


    def damage_explosive_spider(self, amount : int):
        if self.meta["timer"] == 0:
            self.meta["timer"] = FRAMERATE * 2
        return 0
        # else:
            # self.meta["timer"] //= 2

    def tick_explosive_spider(self):
        if not "timer" in self.meta.keys():
            self.meta["timer"] = 0

        if self.meta["timer"] == 0:
            distance = math.sqrt(
                (self.x - self.arena.player.x) ** 2 + (self.y - self.arena.player.y) ** 2
            )
            angle = math.atan2(
                self.arena.player.y - self.y, self.arena.player.x - self.x,
            )

            if 12 > distance > 1:
                self.x += 0.05 * math.cos(angle)
                self.y += 0.05 * math.sin(angle)

        if self.meta["timer"] > 0:
            theta = (random.randint(90 - 35, 90 + 35) + 180) / 180 * math.pi
            self.meta["timer"] -= 1
            self.arena.newParticle(
                f"flame{random.randint(0, 2)}",
                self.x, self.y,
                0.15 * math.cos(theta),
                0.15 * math.sin(theta),
                FRAMERATE // 4,
            )

            if self.meta["timer"] == 0:
                self.destroy = True
                self.arena.flash(self.x, self.y, 120, FRAMERATE // 4)
                self.arena.camera.shake(0.75, FRAMERATE // 2)
                for angle in range(0, 360, 5):
                    self.arena.newEntity(
                        "flameball",
                        self.x + 0.25 * math.cos(angle / 180 * math.pi),
                        self.y + 0.25 * math.sin(angle / 180 * math.pi),
                        angle = angle,
                        velocity = 0.45,
                        duration = FRAMERATE // 4,
                    )
                self.destroyTimer = FRAMERATE# // 2

    def animate_explosive_spider(self):
        if not "timer" in self.meta.keys():
            self.meta["timer"] = 0
        if self.meta["timer"] > 0:
            return "entity_explosive_spider_fuse", 0
        else:
            return "entity_explosive_spider", 0


    def tick_web(self):
        self.x += self.meta.get("velocity", 0.15) * math.cos(self.meta.get("angle", 0) / 180 * math.pi)
        self.y += self.meta.get("velocity", 0.15) * math.sin(self.meta.get("angle", 0) / 180 * math.pi)

        distance = math.sqrt((self.x - self.arena.player.x) ** 2 + (self.y - self.arena.player.y) ** 2)
        if distance <= (self.arena.player.w + self.arena.player.h) / 2:
            self.arena.player.damage(1)
            self.arena.player.knockback(0.15, self.meta.get("angle", 0), FRAMERATE // 8)
            self.destroy = True

        if self.timer >= self.meta.get("duration", FRAMERATE // 4):
            self.destroy = True

        for block in self.arena.player.getRoom().layout:
            if block.x - block.w / 2 < self.x < block.x + block.w / 2:
                if block.y - block.h / 2 < self.y < block.y + block.h / 2:
                    self.destroy = True
                    break


    def tick_bullet(self):
        self.x += self.meta.get("velocity", 0.15) * math.cos(self.meta.get("angle", 0) / 180 * math.pi)
        self.y += self.meta.get("velocity", 0.15) * math.sin(self.meta.get("angle", 0) / 180 * math.pi)

        for entity in self.arena.player.getRoom().entities:
            if not entity.ghostlike: continue
            if math.sqrt((self.x - entity.x) ** 2 + (self.y - entity.y) ** 2) <= (entity.w + entity.h) / 2:
                entity.damage(1, self.meta.get("angle", 0))
                entity.knockback(0.35, self.meta.get("angle", 0), FRAMERATE // 8)
                self.destroy = True

        if self.timer >= self.meta.get("duration", FRAMERATE // 4):
            self.destroy = True

        for block in self.arena.player.getRoom().layout:
            if block.x - block.w / 2 < self.x < block.x + block.w / 2:
                if block.y - block.h / 2 < self.y < block.y + block.h / 2:
                    self.destroy = True
                    break

    def damage_bullet(self, amount : int):
        return 0

    def animate_bullet(self):
        return "entity_bullet", self.meta.get("angle", 0)


    def tick_dagger(self):
        self.x += self.meta.get("velocity", 0.15) * math.cos(self.meta.get("angle", 0) / 180 * math.pi)
        self.y += self.meta.get("velocity", 0.15) * math.sin(self.meta.get("angle", 0) / 180 * math.pi)

        for entity in self.arena.player.getRoom().entities:
            if not entity.ghostlike: continue
            if math.sqrt((self.x - entity.x) ** 2 + (self.y - entity.y) ** 2) <= (entity.w + entity.h) / 2:
                entity.damage(2, self.meta.get("angle", 0))
                entity.knockback(0.35, self.meta.get("angle", 0), FRAMERATE // 8)
                # self.destroy = True #

        if self.timer >= self.meta.get("duration", FRAMERATE // 4):
            self.destroy = True

        for block in self.arena.player.getRoom().layout:
            if block.x - block.w / 2 < self.x < block.x + block.w / 2:
                if block.y - block.h / 2 < self.y < block.y + block.h / 2:
                    self.destroy = True
                    break

    def damage_dagger(self, amount : int):
        return 0

    def animate_dagger(self):
        return "dagger", -(self.meta.get("angle", 0) + 90)


    def tick_flameball(self):
        self.x += self.meta.get("velocity", 0.15) * math.cos(self.meta.get("angle", 0) / 180 * math.pi)
        self.y += self.meta.get("velocity", 0.15) * math.sin(self.meta.get("angle", 0) / 180 * math.pi)

        self.arena.newParticle(
            f"flame{random.randint(0, 2)}",
            self.x, self.y, 0, 0, self.meta.get("duration", FRAMERATE // 4) // 8,
        )

        for entity in self.arena.player.getRoom().entities:
            if not entity.ghostlike: continue
            if math.sqrt((self.x - entity.x) ** 2 + (self.y - entity.y) ** 2) <= (entity.w + entity.h) / 2:
                entity.damage(2, self.meta.get("angle", 0))
                entity.knockback(0.25, self.meta.get("angle", 0), FRAMERATE // 8)
                self.destroy = True

        distance = math.sqrt((self.x - self.arena.player.x) ** 2 + (self.y - self.arena.player.y) ** 2)
        if distance <= (self.arena.player.w + self.arena.player.h) / 2:
            self.arena.player.damage(2)
            self.arena.player.knockback(0.25, self.meta.get("angle", 0), FRAMERATE // 8)
            self.destroy = True

        if self.timer >= self.meta.get("duration", FRAMERATE // 4):
            self.destroy = True

        for block in self.arena.player.getRoom().layout:
            if block.x - block.w / 2 < self.x < block.x + block.w / 2:
                if block.y - block.h / 2 < self.y < block.y + block.h / 2:
                    self.destroy = True
                    break

    def damage_flameball(self, amount : int):
        return 0

    def animate_flameball(self):
        return "entity_flameball", -(self.meta.get("angle", 0) + 90)


    def damage_methane_can(self, amount : int):
        if self.meta["timer"] == 0:
            self.meta["timer"] = FRAMERATE * 2
        return 0
        # else:
            # self.meta["timer"] //= 2

    def tick_methane_can(self):
        if not "timer" in self.meta.keys():
            self.meta["timer"] = 0

        if self.meta["timer"] > 0:
            theta = (random.randint(90 - 35, 90 + 35) + 180) / 180 * math.pi
            self.meta["timer"] -= 1
            self.arena.newParticle(
                f"flame{random.randint(0, 2)}",
                self.x, self.y,
                0.15 * math.cos(theta),
                0.15 * math.sin(theta),
                FRAMERATE // 4,
            )

            if self.meta["timer"] == 0:
                self.destroy = True
                self.arena.flash(self.x, self.y, 120, FRAMERATE // 4)
                self.arena.camera.shake(0.75, FRAMERATE // 2)
                for angle in range(0, 360, 5):
                    self.arena.newEntity(
                        "flameball",
                        self.x, self.y,
                        angle = angle,
                        velocity = 0.25,
                        duration = FRAMERATE * 2,
                    )

    def animate_methane_can(self):
        if self.meta["timer"] > 0:
            return "entity_methane_can_fuse", 0
        else:
            return "entity_methane_can", 0

    def interact_methane_can(self):

        if self.arena.player.item:

            swap = self.arena.player.item.id
            self.arena.player.item.id = "methane_can"
            self.arena.player.item.loadData()
            self.arena.newEntity("item", self.x, self.y, item_id = swap)
            self.destroy = True

        else:

            self.destroy = True
            self.arena.player.item = Item(self.arena, "methane_can")

        return


    def damage_barricade(self, amount : int):
        return 0

    def tick_barricade(self):
        if self.arena.countOpponents() == 0:
            self.destroy = True

        angle = math.atan2(
            self.y - self.arena.player.y, self.x - self.arena.player.x,
        ) + math.pi
        distance = math.sqrt(
            (self.x - self.arena.player.x) ** 2 + (self.y - self.arena.player.y) ** 2,
        )

        if distance <= (self.arena.player.w + self.arena.player.h) / 2:
            self.arena.player.knockback(0.45, angle * 180 / math.pi, FRAMERATE // 3)
            self.arena.player.hitstun(FRAMERATE // 3)


    def tick_item(self):
        if not "base" in self.meta.keys():
            self.meta["base"] = self.y

        self.y = self.meta["base"] + 0.15 * math.sin(math.pi * (self.timer / FRAMERATE))
        return

    def animate_item(self):
        return f"item_{self.meta.get('item_id')}", 0

    def interact_item(self):

        if self.arena.player.item:

            swap = self.arena.player.item.id
            self.arena.player.item.id = self.meta.get("item_id")
            self.arena.player.item.loadData()
            self.meta["item_id"] = swap

        else:

            self.destroy = True
            self.arena.player.item = Item(self.arena, self.meta["item_id"])

        return


    def damage_dungeon_chest(self, amount : int):
        return 0

    def tick_dungeon_chest(self):
        if not "opened" in self.meta.keys():
            self.meta["opened"] = False

        if self.arena.countOpponents() == 0 and not self.meta["opened"]:
            totaldrop = random.randint(1, 7)
            for e in range(totaldrop):
                angle = 2 * math.pi * e / totaldrop
                item_id = rollGeneration(RANDOMDATA.get("loot").get("dungeon"))
                self.arena.newEntity(
                    "item",
                    self.x + 2.25 * math.cos(angle),
                    self.y + 2.25 * math.sin(angle),
                    item_id = item_id,
                )
            self.meta["opened"] = True
            # self.destroy = True

    def animate_dungeon_chest(self):
        if not "opened" in self.meta.keys():
            self.meta["opened"] = False

        if self.meta["opened"]:
            return "entity_dungeon_chest_open", 0
        else:
            return "entity_dungeon_chest", 0


    def damage_grenade(self, amount : int):
        return 0

    def tick_grenade(self):
        if not "timer" in self.meta.keys():
            self.meta["timer"] = FRAMERATE * 3

        if self.meta["timer"] > 0:
            theta = (random.randint(90 - 35, 90 + 35) + 180) / 180 * math.pi
            self.meta["timer"] -= 1
            self.arena.newParticle(
                f"flame{random.randint(0, 2)}",
                self.x, self.y,
                0.15 * math.cos(theta),
                0.15 * math.sin(theta),
                FRAMERATE // 4,
            )

            if self.meta["timer"] == 0:
                self.destroy = True
                self.arena.flash(self.x, self.y, 120, FRAMERATE // 4)
                self.arena.camera.shake(0.75, FRAMERATE // 2)
                for angle in range(0, 360, 5):
                    self.arena.newEntity(
                        "flameball",
                        self.x + 0.25 * math.cos(angle / 180 * math.pi),
                        self.y + 0.25 * math.sin(angle / 180 * math.pi),
                        angle = angle,
                        velocity = 0.45,
                        duration = FRAMERATE // 4,
                    )


    def damage_turret(self, amount : int):
        return 0

    def tick_turret(self):
        if not "angle" in self.meta.keys():
            self.meta["angle"] = 0
        if not "timer" in self.meta.keys():
            self.meta["timer"] = 0
        self.arena.newParticle("turret_base", self.x, self.y + 0.3, 0, 0, 2)

        target = None
        targetdist = 99999

        for entity in self.arena.player.getRoom().entities:
            if not entity.opponent: continue
            dist = math.sqrt((self.x - entity.x) ** 2 + (self.y - entity.y) ** 2)
            if dist < targetdist:
                targetdist = dist
                target = entity

        if not target:
            self.meta["angle"] = 0
            self.meta["timer"] = 0

        else:
            angle = math.atan2(
                self.y - target.y, self.x - target.x,
            ) * 180 / math.pi
            # print(target.id, angle) #
            self.meta["angle"] = angle

            if self.meta["timer"] > 0:
                self.meta["timer"] -= 1
            else:
                self.meta["timer"] = FRAMERATE // 7

                self.arena.flash(
                    self.x + 0.75 * math.cos(angle / 180 * math.pi + math.pi),
                    self.y + 0.75 * math.sin(angle / 180 * math.pi + math.pi),
                    120, FRAMERATE // 4,
                )
                self.arena.camera.shake(0.05, FRAMERATE // 8)

                self.arena.newEntity(
                    "bullet",
                    self.x + 0.75 * math.cos(angle / 180 * math.pi + math.pi),
                    self.y + 0.75 * math.sin(angle / 180 * math.pi + math.pi),
                    angle = angle + 180,
                    velocity = 0.45,
                    duration = FRAMERATE,
                )

        # print(self.meta["timer"])

    def animate_turret(self):
        if not "angle" in self.meta.keys():
            self.meta["angle"] = 0
        if not "timer" in self.meta.keys():
            self.meta["timer"] = 0
        return "entity_turret", -(self.meta["angle"] + 180)

    def interact_turret(self):

        if self.arena.player.item:

            swap = self.arena.player.item.id
            self.arena.player.item.id = "turret"
            self.arena.player.item.loadData()
            self.arena.newEntity("item", self.x, self.y, item_id = swap)
            self.destroy = True

        else:

            self.destroy = True
            self.arena.player.item = Item(self.arena, "turret")

        return


    def tick_rocket(self):
        self.x += self.meta.get("velocity", 0.15) * math.cos(self.meta.get("angle", 0) / 180 * math.pi)
        self.y += self.meta.get("velocity", 0.15) * math.sin(self.meta.get("angle", 0) / 180 * math.pi)

        self.arena.newParticle(
            f"flame{random.randint(0, 2)}",
            self.x, self.y, 0, 0, self.meta.get("duration", FRAMERATE // 4) // 8,
        )

        for entity in self.arena.player.getRoom().entities:
            if not entity.ghostlike: continue
            if math.sqrt((self.x - entity.x) ** 2 + (self.y - entity.y) ** 2) <= (entity.w + entity.h) / 2:
                entity.damage(2, self.meta.get("angle", 0))
                entity.knockback(0.25, self.meta.get("angle", 0), FRAMERATE // 8)
                self.destroy = True

        distance = math.sqrt((self.x - self.arena.player.x) ** 2 + (self.y - self.arena.player.y) ** 2)
        if distance <= (self.arena.player.w + self.arena.player.h) / 2:
            self.arena.player.damage(2)
            self.arena.player.knockback(0.25, self.meta.get("angle", 0), FRAMERATE // 8)
            self.destroy = True

        if self.timer >= self.meta.get("duration", FRAMERATE // 4):
            self.destroy = True

        for block in self.arena.player.getRoom().layout:
            if block.x - block.w / 2 < self.x < block.x + block.w / 2:
                if block.y - block.h / 2 < self.y < block.y + block.h / 2:
                    self.destroy = True
                    break

        if self.destroy == True:
            self.arena.flash(self.x, self.y, 120, FRAMERATE)
            self.arena.camera.shake(0.75, FRAMERATE // 4)
            for angle in range(0, 360, 5):
                self.arena.newEntity(
                    "flameball",
                    self.x + 0.25 * math.cos(angle / 180 * math.pi),
                    self.y + 0.25 * math.sin(angle / 180 * math.pi),
                    angle = angle,
                    velocity = 0.25,
                    duration = FRAMERATE // 4,
                )

    def damage_rocket(self, amount : int):
        return 0

    def animate_rocket(self):
        return "entity_rocket", self.meta.get("angle", 0)


    def damage_aura_wisp(self, amount : int):
        return 0

    def tick_aura_wisp(self):
        if not "angle" in self.meta.keys():
            self.meta["angle"] = 0

        if not self.arena.player.item:
            self.destroy = True
            return
        if self.arena.player.item.id != "aura_blade":
            self.destroy = True
            return

        self.meta["angle"] += 3
        if self.meta["angle"] > 360:
            self.meta["angle"] -= 360

        self.x = self.arena.player.x + 1.75 * math.cos(self.meta["angle"] / 180 * math.pi)
        self.y = self.arena.player.y + 1.75 * math.sin(self.meta["angle"] / 180 * math.pi)


        for entity in self.arena.player.getRoom().entities:
            if not entity.opponent: continue
            distance = math.sqrt((entity.x - self.x) ** 2 + (entity.y - self.y) ** 2)
            if distance > (entity.w + entity.h) / 2: continue
            angle = math.atan2(
                self.arena.player.y - entity.y, self.arena.player.x - entity.x,
            ) * 180 / math.pi
            entity.damage(1, angle)
            entity.knockback(0.25, angle + 180, FRAMERATE // 4)