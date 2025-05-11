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
arena.saveGame()
arena.camera.shake(0.5, FRAMERATE * 2)

running = True
while running:

    mouseX, mouseY = pygame.mouse.get_pos()
    mouseAngle = math.atan2(
        mouseY - HEIGHT // 2, mouseX - WIDTH // 2,
    )

    for e in pygame.event.get():

        if e.type == pygame.KEYDOWN:

            if e.key == pygame.K_ESCAPE:
                running = False
                pygame.quit()
                break

    if not running: break

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

    for block in arena.player.getRoom().layout:
        pygame.draw.rect(
            screen, "#FFFFFF",
            (
                (block.x - block.w / 2 - camX) * arena.scale + WIDTH // 2,
                (block.y - block.h / 2 - camY) * arena.scale + HEIGHT // 2,
                block.w * arena.scale,
                block.h * arena.scale,
            )
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

    if arena.player.item:

        img = IMAGES.get(f"item_{arena.player.item.id}")
        img = pygame.transform.rotate(img, -90)
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



    img = IMAGES.get("aim")
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