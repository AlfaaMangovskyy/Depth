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
        self.light : list[Light] = []

    def tick(self):
        for entity in self.entities:
            entity.tick()
            if entity.destroy:
                if entity.destroyTimer == 0:
                    self.entities.remove(entity)
                    del entity
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
        self.stun : int = 0

        self.kb : int = 0
        self.kbangle : int = 0
        self.kbforce : float = 0.0

        self.hp : int = 12
        self.eliminated : bool = False

    def getRoom(self):
        return self.arena.getRoom(self.rx, self.ry)

    def moveX(self, dx : float):
        if self.stun > 0: return
        self.x += dx

    def moveY(self, dy : float):
        if self.stun > 0: return
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

    def apply_shotgun(self, point : tuple[float, float]):
        angle = math.atan2(
            self.arena.player.y - point[1], self.arena.player.x - point[0],
        ) + math.pi
        shotX = self.arena.player.x + math.cos(angle)
        shotY = self.arena.player.y + math.sin(angle)

        self.arena.flash(shotX, shotY, 120, FRAMERATE // 4)
        self.arena.player.knockback(0.25, (angle + math.pi) * 180 / math.pi, FRAMERATE // 8)
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
        self.damageable : bool = self._data.get("damage", True)
        self.interactable : bool = self._data.get("interact", False)

        self.kb : int = 0
        self.kbangle : int = 0
        self.kbforce : float = 0.0

        self.destroy = False
        self.destroyTimer : int = 0

        self.timer : int = 0

    def knockback(self, force : float, angle : int, duration : int):
        self.kbforce = force
        self.kbangle = angle
        self.kb = duration

    def tick(self) -> None:
        if self.destroyTimer > 0:
            self.destroyTimer -= 1
            return
        f = getattr(self, f"tick_{self.id}", self.tick_null)()
        self.timer += 1

        if self.damageable:

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

    def damage(self, amount : int) -> int:
        if self.destroyTimer > 0: return
        return getattr(self, f"damage_{self.id}", self.damage_null)(amount)

    def interact(self):
        if not self.interactable: return
        return getattr(self, f"interact_{self.id}", self.interact_null)()

    def animate(self) -> str:
        # if self.damageable:
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

    def animate_null(self) -> str:
        return f"entity_{self.id}"

    def interact_null(self):
        return


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


    def tick_bullet(self):
        self.x += self.meta.get("velocity", 0.15) * math.cos(self.meta.get("angle", 0) / 180 * math.pi)
        self.y += self.meta.get("velocity", 0.15) * math.sin(self.meta.get("angle", 0) / 180 * math.pi)

        for entity in self.arena.player.getRoom().entities:
            if not entity.damageable: continue
            if math.sqrt((self.x - entity.x) ** 2 + (self.y - entity.y) ** 2) <= (entity.w + entity.h) / 2:
                entity.damage(1)
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


    def tick_flameball(self):
        self.x += self.meta.get("velocity", 0.15) * math.cos(self.meta.get("angle", 0) / 180 * math.pi)
        self.y += self.meta.get("velocity", 0.15) * math.sin(self.meta.get("angle", 0) / 180 * math.pi)

        for entity in self.arena.player.getRoom().entities:
            if not entity.damageable: continue
            if math.sqrt((self.x - entity.x) ** 2 + (self.y - entity.y) ** 2) <= (entity.w + entity.h) / 2:
                entity.damage(3)
                entity.knockback(0.35, self.meta.get("angle", 0), FRAMERATE // 8)
                self.destroy = True

        distance = math.sqrt((self.x - self.arena.player.x) ** 2 + (self.y - self.arena.player.y) ** 2)
        if distance <= (self.arena.player.w + self.arena.player.h) / 2:
            self.arena.player.damage(3)
            self.arena.player.knockback(0.35, self.meta.get("angle", 0), FRAMERATE // 8)
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


    def damage_methane_can(self, amount : int):
        self.meta["timer"] = FRAMERATE * 2

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
                        velocity = 0.45,
                        duration = FRAMERATE,
                    )

    def animate_methane_can(self):
        if self.meta["timer"] > 0:
            return "entity_methane_can_fuse"
        else:
            return "entity_methane_can"


    def tick_item(self):
        if not "base" in self.meta.keys():
            self.meta["base"] = self.y

        self.y = self.meta["base"] + 0.15 * math.sin(math.pi * (self.timer / FRAMERATE))
        return

    def animate_item(self):
        return f"item_{self.meta.get('item_id')}"

    def interact_item(self):
        swap = self.arena.player.item.id
        self.arena.player.item.id = self.meta.get("item_id")
        self.meta["item_id"] = swap
        return