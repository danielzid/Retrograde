import pygame
from body import Body
from physics import compute_gravity
from math import sqrt

pygame.init()
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

bodies = []
spawning = False
spawn_x = spawn_y = 0

running = True
while running:
    dt = clock.tick(60) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            spawning = True
            spawn_x, spawn_y = pygame.mouse.get_pos()

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if spawning:
                mx, my = pygame.mouse.get_pos()
                vx = (mx - spawn_x) * 0.02
                vy = (my - spawn_y) * 0.02
                bodies.append(Body(spawn_x, spawn_y, vx, vy, mass=50, radius=5))
                spawning = False

    ax, ay = compute_gravity(bodies, G=1.3, soften=30)

    for i, b in enumerate(bodies):
        b.update(ax[i], ay[i], dt)

    screen.fill((0, 0, 0))
    for b in bodies:
        b.draw(screen)

    pygame.display.flip()

pygame.quit()
