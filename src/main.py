import pygame
from static import *

import sys
import os

DEBUG = False
for i in ("-d", "-debug"):
    if i in sys.argv:
        DEBUG = True
        break

pygame.init()
screen = pygame.display.set_mode(
    (WIDTH, HEIGHT), pygame.NOFRAME,
)
clock = pygame.time.Clock()
pygame.mouse.set_visible(0)

IMAGES = {
    _id.removesuffix(".png") : pygame.image.load(f"src/make/{_id}").convert_alpha() for _id in os.listdir("src/make")
}

arena = Arena("src/gsave.json")
# arena.newEntity("methane_can", 4, 4)
# arena.newEntity("item", 4, 4, item_id = "sword")
arena.saveGame()
# arena.camera.shake(0.5, FRAMERATE * 2)
# arena.flash(2, 2, 120, 10)

mouseL = False
mouseR = False

running = True
while running:

    mouseX, mouseY = pygame.mouse.get_pos()
    mouseAngle = math.atan2(
        mouseY - HEIGHT // 2, mouseX - WIDTH // 2,
    )
    camX, camY = arena.camera.get()

    for e in pygame.event.get():

        if e.type == pygame.KEYDOWN:

            if e.key == pygame.K_ESCAPE:
                running = False
                pygame.quit()
                break

        if e.type == pygame.MOUSEBUTTONDOWN:

            if e.button == 1:
                mouseL = True
                if arena.player.item:
                    arena.player.item.apply((
                        ((mouseX - WIDTH / 2) / arena.scale) + camX,
                        ((mouseY - HEIGHT / 2) / arena.scale) + camY,
                    ))

            elif e.button == 3:
                mouseR = True
                point = (
                    ((mouseX - WIDTH / 2) / arena.scale) + camX,
                    ((mouseY - HEIGHT / 2) / arena.scale) + camY,
                )
                for entity in arena.player.getRoom().entities:
                    if not entity.interactable: continue
                    distance = math.sqrt((arena.player.x - point[0]) ** 2 + (arena.player.y - point[1]) ** 2)
                    if distance > 7: continue
                    if entity.x - entity.w / 2 <= point[0] <= entity.x + entity.w / 2:
                        if entity.y - entity.h / 2 <= point[1] <= entity.y + entity.h / 2:
                            entity.interact()

        if e.type == pygame.MOUSEBUTTONUP:

            if e.button == 1:
                mouseL = False

            elif e.button == 3:
                mouseR = False

    if not running: break

    if mouseL:
        if arena.player.item:
            arena.player.item.dapply((
                ((mouseX - WIDTH / 2) / arena.scale) + camX,
                ((mouseY - HEIGHT / 2) / arena.scale) + camY,
            ))

    keymap = pygame.key.get_pressed()
    if keymap[pygame.K_w]:
        arena.player.moveY(-arena.player.speed)
    if keymap[pygame.K_a]:
        arena.player.moveX(-arena.player.speed)
    if keymap[pygame.K_s]:
        arena.player.moveY(arena.player.speed)
    if keymap[pygame.K_d]:
        arena.player.moveX(arena.player.speed)

    arena.tick()
    camX, camY = arena.camera.get()

    screen.fill("#030303")

    for x in range(arena.player.getRoom().w):
        for y in range(arena.player.getRoom().h):
            img = IMAGES.get("tile_base")
            screen.blit(
                img, (
                    (x - arena.player.getRoom().w / 2 - camX) * arena.scale + WIDTH // 2,
                    (y - arena.player.getRoom().h / 2 - camY) * arena.scale + HEIGHT // 2,
                )
            )

    for block in arena.player.getRoom().layout:
        # pygame.draw.rect(
        #     screen, "#FFFFFF",
        #     (
        #         (block.x - block.w / 2 - camX) * arena.scale + WIDTH // 2,
        #         (block.y - block.h / 2 - camY) * arena.scale + HEIGHT // 2,
        #         block.w * arena.scale,
        #         block.h * arena.scale,
        #     )
        # )
        for dx in range(math.floor(block.w)):
            for dy in range(math.floor(block.h)):
                img = IMAGES.get("tile_ceil")
                screen.blit(
                    img, (
                        (block.x + dx - block.w / 2 - camX) * arena.scale + WIDTH // 2,
                        (block.y + dy - block.h / 2 - camY) * arena.scale + HEIGHT // 2,
                    )
                )

        # for dx in range(math.floor(block.w)):
        #     # print(block.y + dy - block.h / 2 - 1, arena.player.getRoom().h / 2)
        #     if block.y + dy - 1 != arena.player.getRoom().h / 2:
        #         img = IMAGES.get("tile_wall_front")
        #         screen.blit(
        #             img, (
        #                 (block.x + dx - block.w / 2 - camX) * arena.scale + WIDTH // 2,
        #                 (block.y + dy - block.h / 2 - camY) * arena.scale + HEIGHT // 2,
        #             )
        #         )

        # if block.y + dy - 1 != arena.player.getRoom().h / 2:
        #     pygame.draw.rect(
        #         screen, "#FFFF00",
        #         (
        #             (block.x - block.w / 2 - camX) * arena.scale + WIDTH // 2,
        #             (block.y - block.h / 2 - camY) * arena.scale + HEIGHT // 2,
        #             block.w * arena.scale,
        #             (block.h - 1) * arena.scale + 4,
        #         ), 4,
        #     )
        # else:
        #     pygame.draw.rect(
        #         screen, "#FFFF00",
        #         (
        #             (block.x - block.w / 2 - camX) * arena.scale + WIDTH // 2,
        #             (block.y - block.h / 2 - camY) * arena.scale + HEIGHT // 2,
        #             block.w * arena.scale,
        #             block.h * arena.scale,
        #         ), 4,
        #     )
        pygame.draw.rect(
            screen, "#FFFF00",
            (
                (block.x - block.w / 2 - camX) * arena.scale + WIDTH // 2,
                (block.y - block.h / 2 - camY) * arena.scale + HEIGHT // 2,
                block.w * arena.scale,
                block.h * arena.scale,
            ), 4,
        )

    pygame.draw.rect(
        screen, "#030303",
        (
            (-arena.player.getRoom().w / 2 - camX) * arena.scale + WIDTH // 2 - 2,
            (-arena.player.getRoom().h / 2 - camY) * arena.scale + HEIGHT // 2 - 2,
            arena.player.getRoom().w * arena.scale + 4,
            arena.player.getRoom().h * arena.scale + 4,
        ), 8,
    )

    pygame.draw.rect(
        screen, "#FFFFFF",
        (
            (arena.player.x - arena.player.w / 2 - camX) * arena.scale + WIDTH // 2,
            (arena.player.y - arena.player.h / 2 - camY) * arena.scale + HEIGHT // 2,
            arena.player.w * arena.scale,
            arena.player.h * arena.scale,
        )
    )

    if arena.player.item != None:

        img = IMAGES.get(f"item_{arena.player.item.id}")
        if math.cos(mouseAngle) < 0:
            img = pygame.transform.flip(img, 0, 1)
        img = pygame.transform.rotate(img, 180)
        # img = pygame.transform.rotate(img, -90) #
        img = pygame.transform.rotate(img, mouseAngle * 180 / math.pi)
        img = pygame.transform.flip(img, 0, 1)

        aimX = arena.scale * arena.player.w * math.cos(mouseAngle)
        aimY = arena.scale * arena.player.h * math.sin(mouseAngle)

        screen.blit(
            img, (
                WIDTH // 2 + aimX - img.get_width() // 2,
                HEIGHT // 2 + aimY - img.get_height() // 2,
            )
        )

    for entity in arena.player.getRoom().entities:

        key = entity.animate()

        # print(entity.id, entity.destroyTimer) #
        if entity.destroyTimer > FRAMERATE // 2:
            if f"knockout_{entity.id}" in IMAGES.keys():
                key = f"knockout_{entity.id}"

        elif 1 <= entity.destroyTimer <= FRAMERATE // 2:
            # print(
            #         (entity.x - camX) * arena.scale + WIDTH // 2,
            #         (entity.y - camY) * arena.scale + HEIGHT // 2,
            #     )
            delta = (FRAMERATE // 2 - entity.destroyTimer) / (FRAMERATE // 2) * 10
            pygame.draw.circle(
                screen, "#FFFFFF", (
                    (entity.x - camX) * arena.scale + WIDTH // 2,
                    (entity.y - camY - delta) * arena.scale + HEIGHT // 2,
                ), (entity.w + entity.h) / 4 * arena.scale,
            )
            pygame.draw.polygon(
                screen, "#FFFFFF", (
                    (
                        (entity.x - camX - entity.w / 2) * arena.scale + WIDTH // 2,
                        (entity.y - camY - delta) * arena.scale + HEIGHT // 2,
                    ),
                    (
                        (entity.x - camX + entity.w / 2) * arena.scale + WIDTH // 2,
                        (entity.y - camY - delta) * arena.scale + HEIGHT // 2,
                    ),
                    (
                        (entity.x - camX) * arena.scale + WIDTH // 2,
                        (entity.y - camY + entity.h * 2 - delta) * arena.scale + HEIGHT // 2,
                    ),
                )
            )
            continue

        img = IMAGES.get(key)
        screen.blit(
            img, (
                (entity.x - camX) * arena.scale + WIDTH // 2 - img.get_width() // 2,
                (entity.y - camY) * arena.scale + HEIGHT // 2 - img.get_height() // 2,
            )
        )

    for particle in arena.player.getRoom().particles:

        img = IMAGES.get(f"particle_{particle.id}")
        screen.blit(
            img, (
                (particle.x - camX) * arena.scale + WIDTH // 2 - img.get_width() // 2,
                (particle.y - camY) * arena.scale + HEIGHT // 2 - img.get_height() // 2,
            )
        )

    for light in arena.player.getRoom().light:

        lim = IMAGES.get("light")
        alpha = round((light.lum / 120) * 255)
        lim.set_alpha(alpha)

        screen.blit(
            lim, (
                (light.x - camX) * arena.scale + WIDTH // 2 - lim.get_width() // 2,
                (light.y - camY) * arena.scale + HEIGHT // 2 - lim.get_height() // 2,
            )
        )

    if arena.transtimer > 0:

        if arena.transdir == 0:

            if arena.transtimer > FRAMERATE // 4:
                mul = (arena.transtimer - FRAMERATE // 4) / (FRAMERATE // 4)
                pygame.draw.rect(
                    screen, "#000000",
                    (
                        0, HEIGHT * mul, WIDTH, HEIGHT - HEIGHT * mul,
                    )
                )
            else:
                mul = arena.transtimer / (FRAMERATE // 4)
                pygame.draw.rect(
                    screen, "#000000",
                    (
                        0, 0, WIDTH, HEIGHT * mul,
                    )
                )

        elif arena.transdir == 2:

            if arena.transtimer > FRAMERATE // 4:
                mul = (arena.transtimer - FRAMERATE // 4) / (FRAMERATE // 4)
                pygame.draw.rect(
                    screen, "#000000",
                    (
                        0, 0, WIDTH, HEIGHT - HEIGHT * mul,
                    )
                )
            else:
                mul = arena.transtimer / (FRAMERATE // 4)
                pygame.draw.rect(
                    screen, "#000000",
                    (
                        0, HEIGHT - HEIGHT * mul, WIDTH, HEIGHT * mul,
                    )
                )

        elif arena.transdir == 1:

            if arena.transtimer > FRAMERATE // 4:
                mul = (arena.transtimer - FRAMERATE // 4) / (FRAMERATE // 4)
                pygame.draw.rect(
                    screen, "#000000",
                    (
                        0, 0, WIDTH - WIDTH * mul, HEIGHT,
                    )
                )
            else:
                mul = arena.transtimer / (FRAMERATE // 4)
                pygame.draw.rect(
                    screen, "#000000",
                    (
                        WIDTH - WIDTH * mul, 0, WIDTH * mul, HEIGHT,
                    )
                )

        elif arena.transdir == 3:

            if arena.transtimer > FRAMERATE // 4:
                mul = (arena.transtimer - FRAMERATE // 4) / (FRAMERATE // 4)
                pygame.draw.rect(
                    screen, "#000000",
                    (
                        WIDTH * mul, 0, WIDTH - WIDTH * mul, HEIGHT,
                    )
                )
            else:
                mul = arena.transtimer / (FRAMERATE // 4)
                pygame.draw.rect(
                    screen, "#000000",
                    (
                        0, 0, WIDTH * mul, HEIGHT,
                    )
                )



    img = IMAGES.get("aim")

    point = (
        ((mouseX - WIDTH / 2) / arena.scale) + camX,
        ((mouseY - HEIGHT / 2) / arena.scale) + camY,
    )
    for entity in arena.player.getRoom().entities:
        if not entity.interactable: continue
        distance = math.sqrt((arena.player.x - point[0]) ** 2 + (arena.player.y - point[1]) ** 2)
        if distance > 7: continue
        if entity.x - entity.w / 2 <= point[0] <= entity.x + entity.w / 2:
            if entity.y - entity.h / 2 <= point[1] <= entity.y + entity.h / 2:
                img = IMAGES.get("aim_interact")

    screen.blit(
        img, (
            mouseX - img.get_width() // 2,
            mouseY - img.get_height() // 2,
        )
    )



    if DEBUG:

        pygame.draw.rect(
            screen, "#FF0000",
            (
                (arena.player.x - arena.player.w / 2 - camX) * arena.scale + WIDTH // 2,
                (arena.player.y - arena.player.h / 2 - camY) * arena.scale + HEIGHT // 2,
                arena.player.w * arena.scale,
                arena.player.h * arena.scale,
            ), 4,
        )

        for entity in arena.player.getRoom().entities:

            pygame.draw.rect(
                screen, "#FF0000",
                (
                    (entity.x - entity.w / 2 - camX) * arena.scale + WIDTH // 2,
                    (entity.y - entity.h / 2 - camY) * arena.scale + HEIGHT // 2,
                    entity.w * arena.scale,
                    entity.h * arena.scale,
                ), 4,
            )

        pygame.draw.rect(
            screen, "#FF0000",
            (
                (-arena.player.getRoom().w / 2 - camX) * arena.scale + WIDTH // 2 - 2,
                (-arena.player.getRoom().h / 2 - camY) * arena.scale + HEIGHT // 2 - 2,
                arena.player.getRoom().w * arena.scale + 4,
                arena.player.getRoom().h * arena.scale + 4,
            ), 4,
        )

    pygame.display.update()
    clock.tick(FRAMERATE)